"""main.py — Fleet Snowfluff bot entry point."""

import asyncio
import logging
import os
import sys

# load_dotenv() MUST run before any module that reads env vars at import time (db/session.py)
from dotenv import load_dotenv
load_dotenv()

import discord
from discord import app_commands
from discord.ext import commands

import db
import gemini_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("fleet_snowfluff")

COGS = ["cogs.utility", "cogs.chat", "cogs.summarize", "cogs.aemeath"]


class FleetSnowfluff(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # required for on_message natural chat
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)

    async def setup_hook(self) -> None:
        self.tree.on_error = self.on_app_command_error
        await db.init_db()
        for cog in COGS:
            try:
                await self.load_extension(cog)
                logger.info("Loaded cog: %s", cog)
            except Exception as e:
                logger.exception("Failed to load cog %s: %s", cog, e)
        synced = await self.tree.sync()
        logger.info("Synced %d slash command(s).", len(synced))

    async def on_ready(self) -> None:
        logger.info("Fleet Snowfluff online as %s (ID: %s)", self.user, self.user.id)
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening, name="/help | Powered by Gemini ❄️"
        ))

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        msg = {
            app_commands.MissingPermissions:    "🔒 You don't have permission to use this command.",
            app_commands.BotMissingPermissions: "🔒 I'm missing permissions needed to run this command.",
            app_commands.CheckFailure:          "🔒 You don't have permission to use this command.",
        }.get(type(error), "⚠️ Something went wrong. Please try again.")

        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ On cooldown. Try again in {error.retry_after:.1f}s."

        logger.error("App command error /%s: %s", interaction.command and interaction.command.name, error)
        try:
            sender = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
            await sender(msg, ephemeral=True)
        except discord.HTTPException:
            pass


async def main() -> None:
    token, gemini_key = os.getenv("DISCORD_TOKEN"), os.getenv("GEMINI_API_KEY")
    if not token or not gemini_key:
        logger.critical("DISCORD_TOKEN and GEMINI_API_KEY must be set in .env")
        sys.exit(1)
    gemini_client.configure(gemini_key)
    async with FleetSnowfluff() as bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
