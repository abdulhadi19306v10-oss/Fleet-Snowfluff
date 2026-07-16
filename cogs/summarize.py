"""cogs/summarize.py — /summarize: fetch channel history → Gemini summary."""

import logging
import discord
from discord import app_commands
from discord.ext import commands
import db
import gemini_client

logger = logging.getLogger("fleet_snowfluff.summarize")


class SummarizeCog(commands.Cog, name="Summarize"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="summarize", description="Summarize the last N messages in this channel.")
    @app_commands.describe(count="Number of recent messages to summarize (2–200)")
    async def summarize_command(self, interaction: discord.Interaction, count: app_commands.Range[int, 2, 200] = 50) -> None:
        await interaction.response.defer(thinking=True)
        logger.info("[/summarize] guild=%s channel=%s count=%d user=%s", interaction.guild_id, interaction.channel_id, count, interaction.user)

        lines, total = [], 0
        async for msg in interaction.channel.history(limit=count):
            if not msg.content.strip():
                continue
            line = f"[{msg.author.display_name}]: {msg.content}"
            total += len(line)
            lines.append(line)
            if total >= 12_000:  # ponytail: inline the cap, no named constant needed
                lines.append("... (truncated)")
                break

        if not lines:
            await interaction.followup.send("❌ No readable messages found.", ephemeral=True)
            return

        lines.reverse()  # chronological order
        config = await db.get_guild_config(interaction.guild_id) if interaction.guild_id else {}
        summary = await gemini_client.summarize("\n".join(lines), system_prompt=config.get("system_prompt"))

        embed = discord.Embed(
            title=f"📋 Summary of last {len(lines)} messages",
            description=summary[:4096],
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name} • Powered by Gemini")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SummarizeCog(bot))
