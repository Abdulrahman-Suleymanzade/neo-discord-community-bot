from discord.ext import tasks
from database import add_voice_xp

VOICE_XP_AMOUNT = 10
VOICE_XP_INTERVAL_SECONDS = 300


class VoiceXP:
    def __init__(self, bot, update_level_roles):
        self.bot = bot
        self.update_level_roles = update_level_roles
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

    @tasks.loop(seconds=VOICE_XP_INTERVAL_SECONDS)
    async def loop(self):
        for guild in self.bot.guilds:
            afk_channel = guild.afk_channel

            for channel in guild.voice_channels:
                if afk_channel and channel.id == afk_channel.id:
                    continue

                real_members = [member for member in channel.members if not member.bot]

                if len(real_members) < 2:
                    continue

                for member in real_members:
                    if not member.voice:
                        continue

                    if member.voice.self_mute or member.voice.self_deaf:
                        continue

                    result = add_voice_xp(
                        guild_id=guild.id,
                        user_id=member.id,
                        username=str(member),
                        xp_amount=VOICE_XP_AMOUNT,
                    )

                    if result["leveled_up"]:
                        role_result = await self.update_level_roles(member, result["new_level"])

                        text_channel = guild.system_channel
                        if text_channel:
                            msg = f"🎤 {member.mention} reached **Level {result['new_level']}** from voice activity!"
                            if role_result:
                                msg += f"\n🎁 Role updated: **{role_result}**"
                            await text_channel.send(msg)

    @loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
