import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import init_db, add_xp, get_user_rank, get_leaderboard
from leveling import calculate_level, xp_for_next_level, generate_xp

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it in Render Environment Variables.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    init_db()
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
        await message.channel.send(
            f"💚 {message.author.mention} leveled up to **Level {result['new_level']}**!"
        )

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
    users = get_leaderboard(interaction.guild.id, limit=10)

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

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)
