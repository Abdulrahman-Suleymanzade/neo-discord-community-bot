import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from profile_card import create_profile_card
from voice_xp import VoiceXP

from database import init_db, add_xp, get_user_rank, get_leaderboard, set_user_xp
from leveling import calculate_level, xp_for_next_level, xp_for_level, generate_xp, calculate_prestige, next_prestige_level

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it in Railway Variables.")

OWNER_IDS = {1340747140153999380}

LEVEL_ROLES = {
    5: "🥉Bronze",
    10: "🥈Silver",
    20: "🥇Gold",
    35: "🔷Platinum",
    55: "💎Diamond",
    80: "👑Legend",
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


def xp_for_level(level: int) -> int:
    return (level ** 2) * 25


async def update_level_roles(member: discord.Member, level: int):
    added_roles = []
    removed_roles = []

    try:
        for required_level, role_name in LEVEL_ROLES.items():
            role = discord.utils.get(member.guild.roles, name=role_name)
            if not role:
                continue

            if level >= required_level:
                if role not in member.roles:
                    await member.add_roles(role, reason="XP level role reward")
                    added_roles.append(role.name)
            else:
                if role in member.roles:
                    await member.remove_roles(role, reason="XP level role update")
                    removed_roles.append(role.name)

    except discord.Forbidden:
        print("Missing permission or role hierarchy issue. Move Neo Bot role above XP roles.")

    parts = []
    if added_roles:
        parts.append("Added: " + ", ".join(added_roles))
    if removed_roles:
        parts.append("Removed: " + ", ".join(removed_roles))

    return " | ".join(parts) if parts else None


@bot.event
async def on_ready():
    init_db()

    if not hasattr(bot, "voice_xp"):
        bot.voice_xp = VoiceXP(bot, update_level_roles)

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as error:
        print(f"Slash command sync failed: {error}")

    print(f"{bot.user} is online.")


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    xp_gained = generate_xp()
    result = add_xp(
        guild_id=message.guild.id,
        user_id=message.author.id,
        username=str(message.author),
        xp_amount=xp_gained,
    )

    if result["leveled_up"]:
        role_name = await update_level_roles(message.author, result["new_level"])

        text = f"💚 {message.author.mention} leveled up to **Level {result['new_level']}**!"
        if role_name:
            text += f"\n🎁 Role updated: **{role_name}**"

        await message.channel.send(text)

    await bot.process_commands(message)


@bot.tree.command(name="rank", description="Show your XP rank.")
async def rank(interaction: discord.Interaction):
    data = get_user_rank(interaction.guild.id, interaction.user.id)

    if not data:
        await interaction.response.send_message("You do not have XP yet. Send messages to start earning XP.")
        return

    level = calculate_level(data["xp"])
    next_xp = xp_for_next_level(level)

    embed = discord.Embed(
        title="💚 Your Rank",
        description=f"**{interaction.user.display_name}**",
        color=0x2ECC71,
    )
    embed.add_field(name="Level", value=str(level), inline=True)
    embed.add_field(name="XP", value=f"{data['xp']} / {next_xp}", inline=True)
    embed.add_field(name="Server Rank", value=f"#{data['rank']}", inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="leaderboard", description="Show the top XP users.")
async def leaderboard(interaction: discord.Interaction):
    users = get_leaderboard(interaction.guild.id, limit=10, offset=0)

    if not users:
        await interaction.response.send_message("No XP data yet.")
        return

    lines = []
    for index, user in enumerate(users, start=1):
        level = calculate_level(user["xp"])
        lines.append(f"**#{index}** {user['username']} — Level **{level}**, `{user['xp']} XP`")

    embed = discord.Embed(
        title="🏆 XP Leaderboard",
        description="\n".join(lines),
        color=0x2ECC71,
    )
    embed.set_footer(text="Use /top for pages")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="setlevel", description="Set a member's level. Owner only.")
async def setlevel(interaction: discord.Interaction, member: discord.Member, level: int):
    if interaction.user.id not in OWNER_IDS:
        await interaction.response.send_message("❌ You cannot use this command.", ephemeral=True)
        return

    if level < 0:
        await interaction.response.send_message("Level cannot be negative.", ephemeral=True)
        return

    xp = xp_for_level(level)
    data = set_user_xp(interaction.guild.id, member.id, str(member), xp)

    role_name = await update_level_roles(member, level)

    message = f"✅ Set {member.mention} to **Level {level}** with **{data['xp']} XP**."
    if role_name:
        message += f"\n🎁 Role updated: **{role_name}**"

    await interaction.response.send_message(message, ephemeral=True)


class TopView(discord.ui.View):
    def __init__(self, guild_id: int, page: int = 0):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.page = page

    def build_embed(self):
        limit = 10
        offset = self.page * limit
        users = get_leaderboard(self.guild_id, limit=limit, offset=offset)

        if not users:
            description = "No users on this page."
        else:
            lines = []
            for index, user in enumerate(users, start=offset + 1):
                level = calculate_level(user["xp"])
                lines.append(f"**#{index}** {user['username']} — Level **{level}**, `{user['xp']} XP`")
            description = "\n".join(lines)

        embed = discord.Embed(
            title="🏆 XP Top",
            description=description,
            color=0x2ECC71,
        )
        embed.set_footer(text=f"Page {self.page + 1}")
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


@bot.tree.command(name="top", description="Show XP leaderboard pages.")
async def top(interaction: discord.Interaction):
    view = TopView(interaction.guild.id)
    await interaction.response.send_message(embed=view.build_embed(), view=view)


@bot.tree.command(name="profile", description="Show a member profile card.")
async def profile(interaction: discord.Interaction, member: discord.Member | None = None):
    target = member or interaction.user
    await interaction.response.defer()

    data = get_user_rank(interaction.guild.id, target.id)

    if not data:
        await interaction.followup.send(f"{target.mention} does not have XP yet.")
        return

    level = calculate_level(data["xp"])
    prestige = calculate_prestige(level)

    if prestige > 0:
        next_level = next_prestige_level(level)
        current_level_xp = xp_for_level(100 + ((prestige - 1) * 50))
        next_xp = xp_for_level(next_level)
    else:
        current_level_xp = xp_for_level(level)
        next_xp = xp_for_next_level(level)

    current_xp = data["xp"] - current_level_xp
    needed_xp = next_xp - current_level_xp
    
    role_name = "No XP Role"

    if prestige > 0:
        role_name = f"⭐ Prestige {prestige}"
    else:
        for required_level, name in LEVEL_ROLES.items():
            if level >= required_level:
                role_name = name

    avatar_bytes = await target.display_avatar.replace(size=256).read()

    card = create_profile_card(
        username=target.display_name,
        avatar_bytes=avatar_bytes,
        level=f"P{prestige}" if prestige > 0 else level,
        rank=data["rank"],
        total_xp=data["xp"],
        current_xp=current_xp,
        needed_xp=needed_xp,
        role_name=role_name,
        server_name=interaction.guild.name,
    )

    file = discord.File(card, filename="profile.png")
    await interaction.followup.send(file=file)

@bot.tree.command(name="rankroles", description="View all XP role rewards.")
async def rankroles(interaction: discord.Interaction):
    level = 0

    data = get_user_rank(interaction.guild.id, interaction.user.id)
    if data:
        level = calculate_level(data["xp"])

    lines = []
    next_reward = None

    for required_level, role in sorted(LEVEL_ROLES.items(), reverse=True):
        icon = "✅" if level >= required_level else "⬜"
        lines.append(f"{icon} **{role}** — Level **{required_level}**")

    for required_level, role in sorted(LEVEL_ROLES.items()):
        if level < required_level:
            next_reward = f"{role} (Level {required_level})"
            break

    embed = discord.Embed(
        title="💚 XP Rank Roles",
        description="\n".join(lines),
        color=0x2ECC71,
    )

    embed.add_field(name="Your Level", value=f"**{level}**", inline=True)
    embed.add_field(
        name="Next Reward",
        value=next_reward or "🏆 All rewards unlocked!",
        inline=True,
    )

    embed.set_footer(text="Earn XP by chatting and staying in voice channels.")

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)
