"""cogs/utility.py — /ping, /help, /config group."""

import logging
import time
import discord
from discord import app_commands
from discord.ext import commands
import db

logger = logging.getLogger("fleet_snowfluff.utility")


class UtilityCog(commands.Cog, name="Utility"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Check Fleet Snowfluff's latency.")
    async def ping_command(self, interaction: discord.Interaction) -> None:
        t = time.monotonic()
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="WebSocket", value=f"`{self.bot.latency * 1000:.1f} ms`", inline=True)
        embed.add_field(name="Round-trip", value=f"`{(time.monotonic() - t) * 1000:.1f} ms`", inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="Show all Fleet Snowfluff commands.")
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="❄️ Fleet Snowfluff — Commands",
            description="Powered by Google Gemini.",
            color=discord.Color.from_rgb(100, 180, 255),
        )
        embed.add_field(name="💬 Chat", inline=False, value=(
            "`/chat <message>` — Chat with me (per-channel memory)\n"
            "`/clearchat` — Wipe this channel's memory"
        ))
        embed.add_field(name="📋 Summarize", inline=False, value="`/summarize [count]` — Summarize last N messages (default 50, max 200)")
        embed.add_field(name="⚙️ Config (Admins)", inline=False, value=(
            "`/config setchannel` `/removechannel` `/listchannels`\n"
            "`/config setpersona` `/clearpersona` `/showpersona`"
        ))
        embed.add_field(name="🛠️ Utility", inline=False, value="`/ping` — Latency check")
        await interaction.response.send_message(embed=embed)

    # ── /config group ──────────────────────────────────────────────────────

    config_group = app_commands.Group(
        name="config",
        description="Per-server Fleet Snowfluff settings.",
        default_permissions=discord.Permissions(manage_guild=True),
        guild_only=True,
    )

    @config_group.command(name="setchannel", description="Enable natural chat in a channel.")
    @app_commands.describe(channel="Channel to enable")
    async def config_setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        cfg = await db.get_guild_config(interaction.guild_id)
        enabled = cfg.get("enabled_channels") or []
        if channel.id in enabled:
            await interaction.response.send_message(f"✅ {channel.mention} already enabled.", ephemeral=True)
            return
        await db.set_enabled_channels(interaction.guild_id, enabled + [channel.id])
        await interaction.response.send_message(f"✅ {channel.mention} added.", ephemeral=True)

    @config_group.command(name="removechannel", description="Disable natural chat in a channel.")
    @app_commands.describe(channel="Channel to remove")
    async def config_removechannel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        cfg = await db.get_guild_config(interaction.guild_id)
        enabled = cfg.get("enabled_channels") or []
        if channel.id not in enabled:
            await interaction.response.send_message(f"❌ {channel.mention} not in list.", ephemeral=True)
            return
        enabled.remove(channel.id)
        await db.set_enabled_channels(interaction.guild_id, enabled or None)
        await interaction.response.send_message(f"✅ {channel.mention} removed.", ephemeral=True)

    @config_group.command(name="listchannels", description="List channels with natural chat enabled.")
    async def config_listchannels(self, interaction: discord.Interaction) -> None:
        cfg = await db.get_guild_config(interaction.guild_id)
        enabled = cfg.get("enabled_channels")
        text = ", ".join(f"<#{c}>" for c in enabled) if enabled else "None configured."
        await interaction.response.send_message(f"📣 Natural-chat channels: {text}", ephemeral=True)

    @config_group.command(name="setpersona", description="Set a custom Gemini persona for this server.")
    @app_commands.describe(prompt="System prompt for Gemini")
    async def config_setpersona(self, interaction: discord.Interaction, prompt: str) -> None:
        await db.set_system_prompt(interaction.guild_id, prompt)
        await interaction.response.send_message(f"✅ Persona set:\n> {prompt[:300]}", ephemeral=True)

    @config_group.command(name="clearpersona", description="Reset to default Fleet Snowfluff persona.")
    async def config_clearpersona(self, interaction: discord.Interaction) -> None:
        await db.set_system_prompt(interaction.guild_id, None)
        await interaction.response.send_message("✅ Persona reset to default.", ephemeral=True)

    @config_group.command(name="showpersona", description="Show the current Gemini system prompt.")
    async def config_showpersona(self, interaction: discord.Interaction) -> None:
        cfg = await db.get_guild_config(interaction.guild_id)
        prompt = cfg.get("system_prompt")
        text = f"**Current persona:**\n```\n{prompt[:1800]}\n```" if prompt else "Using the **default** Fleet Snowfluff persona."
        await interaction.response.send_message(text, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    cog = UtilityCog(bot)
    bot.tree.add_command(cog.config_group)
    await bot.add_cog(cog)
