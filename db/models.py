# db/models.py — SQLAlchemy ORM models for Fleet Snowfluff.
# Designed to work with any dialect: sqlite+aiosqlite (default) or postgresql+asyncpg.
# BigInteger maps to INTEGER on SQLite, BIGINT on Postgres. JSON maps to TEXT/JSONB accordingly.

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int]      = mapped_column(BigInteger, nullable=False, index=True)
    role:       Mapped[str]      = mapped_column(String(10), nullable=False)   # 'user' | 'model'
    content:    Mapped[str]      = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class GuildConfig(Base):
    __tablename__ = "guild_config"

    guild_id:         Mapped[int]        = mapped_column(BigInteger, primary_key=True)
    # JSON stores as TEXT on SQLite, native JSONB on Postgres — no code changes needed when migrating
    enabled_channels: Mapped[list | None] = mapped_column(JSON, nullable=True, default=None)
    system_prompt:    Mapped[str | None]  = mapped_column(Text, nullable=True, default=None)
