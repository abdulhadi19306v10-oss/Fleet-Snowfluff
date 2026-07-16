"""cogs/chat.py — /chat, /clearchat, and natural mention/channel auto-response."""

import logging
import discord
from discord import app_commands
from discord.ext import commands
import db
import gemini_client
import utils

logger = logging.getLogger("fleet_snowfluff.chat")
HISTORY_LIMIT = 20


def _chunks(text: str, size: int = 1990) -> list[str]:
    # ponytail: one util to avoid duplicating the split logic twice
    return [text[i:i + size] for i in range(0, len(text), size)]


class ChatCog(commands.Cog, name="Chat"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="chat", description="Chat with Fleet Snowfluff (Gemini-powered).")
    @app_commands.describe(message="Your message to Fleet Snowfluff")
    @utils.admin_or_master()
    async def chat_command(self, interaction: discord.Interaction, message: str) -> None:
        await interaction.response.defer(thinking=True, ephemeral=False)
        cid = interaction.channel_id
        config = await db.get_guild_config(interaction.guild_id) if interaction.guild_id else {}
        history = await db.get_history(cid, limit=HISTORY_LIMIT)
        reply = await gemini_client.chat(message, history=history, system_prompt=config.get("system_prompt"))
        await db.save_chat(cid, message, reply)
        logger.info("[/chat] guild=%s channel=%s user=%s", interaction.guild_id, cid, interaction.user)
        for chunk in _chunks(reply):
            await interaction.followup.send(chunk, ephemeral=False)

    @app_commands.command(name="clearchat", description="Clear Fleet Snowfluff's memory for this channel.")
    @utils.admin_or_master()
    async def clearchat_command(self, interaction: discord.Interaction) -> None:
        deleted = await db.clear_history(interaction.channel_id)
        await interaction.response.send_message(f"🧹 Cleared **{deleted}** stored messages.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        mentioned = self.bot.user in message.mentions
        is_reply = False
        if message.reference and isinstance(message.reference.resolved, discord.Message):
            res = message.reference.resolved
            if res.author == self.bot.user:
                # Only trigger on replies to /chat command or natural chat replies (which have a reference)
                if res.interaction and res.interaction.name == "chat":
                    is_reply = True
                elif hasattr(res, "interaction_metadata") and res.interaction_metadata and res.interaction_metadata.name == "chat":
                    is_reply = True
                elif res.reference is not None:
                    is_reply = True

        in_channel = False
        if message.guild:
            cfg = await db.get_guild_config(message.guild.id)
            in_channel = bool(cfg.get("enabled_channels") and message.channel.id in cfg["enabled_channels"])

        if not mentioned and not in_channel and not is_reply:
            return

        text = message.content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
        if not text:
            await message.reply("Hey! You mentioned me — what's up? 😊")
            return

        config = await db.get_guild_config(message.guild.id) if message.guild else {}
        history = await db.get_history(message.channel.id, limit=HISTORY_LIMIT)
        logger.info("[mention] guild=%s channel=%s user=%s", message.guild and message.guild.id, message.channel.id, message.author)

        async with message.channel.typing():
            reply = await gemini_client.chat(text, history=history, system_prompt=config.get("system_prompt"))

        await db.save_chat(message.channel.id, text, reply)

        chunks = _chunks(reply)
        await message.reply(chunks[0])
        for chunk in chunks[1:]:
            await message.channel.send(chunk)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ChatCog(bot))
