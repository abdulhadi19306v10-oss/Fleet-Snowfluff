"""cogs/aemeath.py — Automated Aemeath GIF posting loop."""

import logging
import random
from datetime import datetime, timedelta
import discord
from discord import app_commands
from discord.ext import commands, tasks
import db
import utils

logger = logging.getLogger("fleet_snowfluff.aemeath")


class AemeathCog(commands.Cog, name="Aemeath"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.last_sent = {}  # channel_id -> datetime
        self.gif_loop.start()

    def cog_unload(self):
        self.gif_loop.cancel()

    @tasks.loop(minutes=1)
    async def gif_loop(self):
        gifs = await db.get_all_aemeath_gifs()
        if not gifs:
            return
        
        configs = await db.get_aemeath_configs()
        now = datetime.now()
        
        for cfg in configs:
            interval = cfg["interval"]
            for cid in cfg["channels"]:
                last = self.last_sent.get(cid)
                if not last or now - last >= timedelta(minutes=interval):
                    channel = self.bot.get_channel(cid)
                    if channel:
                        try:
                            await channel.send(random.choice(gifs))
                            self.last_sent[cid] = now
                        except Exception as e:
                            logger.error(f"Failed to send GIF to {cid}: {e}")

    @gif_loop.before_loop
    async def before_gif_loop(self):
        await self.bot.wait_until_ready()

    aemeath_group = app_commands.Group(name="aemeath", description="Auto-post random Aemeath GIFs.")

    @aemeath_group.command(name="addgif", description="Add a GIF URL to the global Aemeath pool.")
    @utils.admin_or_master()
    async def addgif_command(self, interaction: discord.Interaction, url: str) -> None:
        await db.add_aemeath_gif(url)
        await interaction.response.send_message(f"✅ GIF added globally!\n{url}", ephemeral=True)

    @aemeath_group.command(name="setchannel", description="Enable auto-GIFs in this channel.")
    @app_commands.describe(channel="Channel to enable")
    @utils.admin_or_master()
    async def setchannel_command(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        cfg = await db.get_guild_config(interaction.guild_id)
        enabled = cfg.get("aemeath_channels") or []
        if channel.id not in enabled:
            enabled.append(channel.id)
            await db.set_aemeath_channels(interaction.guild_id, enabled)
            # Sending one immediately by not setting last_sent
            await interaction.response.send_message(f"✅ Auto-GIFs enabled in {channel.mention}. (Next one coming within a minute!)", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ {channel.mention} is already enabled.", ephemeral=True)

    @aemeath_group.command(name="removechannel", description="Disable auto-GIFs in this channel.")
    @app_commands.describe(channel="Channel to remove")
    @utils.admin_or_master()
    async def removechannel_command(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        cfg = await db.get_guild_config(interaction.guild_id)
        enabled = cfg.get("aemeath_channels") or []
        if channel.id in enabled:
            enabled.remove(channel.id)
            await db.set_aemeath_channels(interaction.guild_id, enabled or None)
            self.last_sent.pop(channel.id, None)
            await interaction.response.send_message(f"✅ Auto-GIFs disabled in {channel.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {channel.mention} is not enabled.", ephemeral=True)

    @aemeath_group.command(name="setinterval", description="Set how often GIFs are posted (in minutes).")
    @app_commands.describe(minutes="Minutes between GIFs")
    @utils.admin_or_master()
    async def setinterval_command(self, interaction: discord.Interaction, minutes: int) -> None:
        if minutes < 1:
            minutes = 1
        await db.set_aemeath_interval(interaction.guild_id, minutes)
        cfg = await db.get_guild_config(interaction.guild_id)
        for cid in cfg.get("aemeath_channels") or []:
            self.last_sent.pop(cid, None)
        await interaction.response.send_message(f"✅ Auto-GIF interval set to **{minutes} minutes**.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AemeathCog(bot))
