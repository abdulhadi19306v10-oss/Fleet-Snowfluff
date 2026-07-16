# Re-export everything from db.session so cogs can just `import db` as before.
from db.session import (
    init_db,
    add_message,
    get_history,
    clear_history,
    prune_history,
    get_guild_config,
    set_enabled_channels,
    set_system_prompt,
)

__all__ = [
    "init_db",
    "add_message",
    "get_history",
    "clear_history",
    "prune_history",
    "get_guild_config",
    "set_enabled_channels",
    "set_system_prompt",
]
