# db/session.py — Async engine/session setup + all ORM query helpers.
# To switch to Postgres: set DATABASE_URL=postgresql+asyncpg://user:pass@host/db in .env.
# No other code changes required.

import logging
import os
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from db.models import Base, ConversationHistory, GuildConfig

logger = logging.getLogger("fleet_snowfluff.db")

_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///fleet_snowfluff.db")
# SQLite needs check_same_thread=False via connect_args; ignored by other dialects
_connect_args = {"check_same_thread": False} if _URL.startswith("sqlite") else {}

engine = create_async_engine(_URL, echo=False, connect_args=_connect_args)
_Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("DB ready  driver=%s", _URL.split(":")[0])


# ── History ──────────────────────────────────────────────────────────────────

async def add_message(channel_id: int, role: str, content: str) -> None:
    async with _Session() as s:
        s.add(ConversationHistory(channel_id=channel_id, role=role, content=content))
        await s.commit()


async def get_history(channel_id: int, limit: int = 20) -> list[dict]:
    """Return last `limit` messages oldest-first, formatted for Gemini's contents list."""
    async with _Session() as s:
        rows = (await s.execute(
            select(ConversationHistory)
            .where(ConversationHistory.channel_id == channel_id)
            .order_by(ConversationHistory.id.desc())
            .limit(limit)
        )).scalars().all()
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


async def clear_history(channel_id: int) -> int:
    async with _Session() as s:
        result = await s.execute(
            delete(ConversationHistory).where(ConversationHistory.channel_id == channel_id)
        )
        await s.commit()
    return result.rowcount


async def prune_history(channel_id: int, keep: int = 40) -> None:
    """Delete all but the most recent `keep` rows for a channel."""
    async with _Session() as s:
        keep_ids = (await s.execute(
            select(ConversationHistory.id)
            .where(ConversationHistory.channel_id == channel_id)
            .order_by(ConversationHistory.id.desc())
            .limit(keep)
        )).scalars().all()
        if keep_ids:
            await s.execute(
                delete(ConversationHistory)
                .where(ConversationHistory.channel_id == channel_id)
                .where(ConversationHistory.id.notin_(keep_ids))
            )
            await s.commit()


# ── Guild Config ──────────────────────────────────────────────────────────────

async def get_guild_config(guild_id: int) -> dict:
    async with _Session() as s:
        cfg = await s.get(GuildConfig, guild_id)
    return {
        "enabled_channels": cfg.enabled_channels if cfg else None,
        "system_prompt":    cfg.system_prompt    if cfg else None,
    }


async def _upsert_config(guild_id: int, **fields) -> None:
    """Generic upsert for GuildConfig — set any subset of columns."""
    async with _Session() as s:
        cfg = await s.get(GuildConfig, guild_id)
        if cfg is None:
            cfg = GuildConfig(guild_id=guild_id)
            s.add(cfg)
        for k, v in fields.items():
            setattr(cfg, k, v)
        await s.commit()


async def set_enabled_channels(guild_id: int, channel_ids: list[int] | None) -> None:
    await _upsert_config(guild_id, enabled_channels=channel_ids)


async def set_system_prompt(guild_id: int, prompt: str | None) -> None:
    await _upsert_config(guild_id, system_prompt=prompt)
