# db/session.py — Async engine/session setup + all ORM query helpers.
# To switch to Postgres: set DATABASE_URL=postgresql+asyncpg://user:pass@host/db in .env.
# No other code changes required.

import logging
import os
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import text
from db.models import Base, ConversationHistory, GuildConfig, AemeathGif

logger = logging.getLogger("fleet_snowfluff.db")

_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///fleet_snowfluff.db")
# SQLite needs check_same_thread=False via connect_args; ignored by other dialects
_connect_args = {"check_same_thread": False} if _URL.startswith("sqlite") else {}

engine = create_async_engine(_URL, echo=False, connect_args=_connect_args)
_Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE guild_config ADD COLUMN aemeath_channels JSON"))
            await conn.execute(text("ALTER TABLE guild_config ADD COLUMN aemeath_interval INTEGER DEFAULT 60"))
        except Exception:
            pass
    logger.info("DB ready  driver=%s", _URL.split(":")[0])


# ── History ──────────────────────────────────────────────────────────────────

async def save_chat(channel_id: int, user_msg: str, model_msg: str) -> None:
    # ponytail: one db transaction for everything, hardcoded 40 limit
    async with _Session() as s:
        s.add_all([
            ConversationHistory(channel_id=channel_id, role="user", content=user_msg),
            ConversationHistory(channel_id=channel_id, role="model", content=model_msg)
        ])
        keep_ids = (await s.execute(select(ConversationHistory.id).where(ConversationHistory.channel_id == channel_id).order_by(ConversationHistory.id.desc()).limit(40))).scalars().all()
        if keep_ids: await s.execute(delete(ConversationHistory).where(ConversationHistory.channel_id == channel_id, ConversationHistory.id.notin_(keep_ids)))
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



# ── Guild Config ──────────────────────────────────────────────────────────────

async def get_guild_config(guild_id: int) -> dict:
    async with _Session() as s:
        cfg = await s.get(GuildConfig, guild_id)
    return {
        "enabled_channels": cfg.enabled_channels if cfg else None,
        "system_prompt":    cfg.system_prompt    if cfg else None,
        "aemeath_channels": cfg.aemeath_channels if cfg else None,
        "aemeath_interval": cfg.aemeath_interval if cfg and cfg.aemeath_interval else 60,
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


async def set_aemeath_channels(guild_id: int, channel_ids: list[int] | None) -> None:
    await _upsert_config(guild_id, aemeath_channels=channel_ids)


async def set_aemeath_interval(guild_id: int, minutes: int) -> None:
    await _upsert_config(guild_id, aemeath_interval=minutes)


async def get_aemeath_configs() -> list[dict]:
    async with _Session() as s:
        rows = (await s.execute(select(GuildConfig).where(GuildConfig.aemeath_channels != None))).scalars().all()
        return [{"guild_id": r.guild_id, "channels": r.aemeath_channels or [], "interval": r.aemeath_interval or 60} for r in rows]


async def add_aemeath_gif(url: str) -> bool:
    async with _Session() as s:
        existing = (await s.execute(select(AemeathGif).where(AemeathGif.url == url))).scalars().first()
        if existing:
            return False
        s.add(AemeathGif(url=url))
        await s.commit()
        return True


async def get_all_aemeath_gifs() -> list[str]:
    async with _Session() as s:
        return list((await s.execute(select(AemeathGif.url))).scalars().all())
