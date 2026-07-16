# Re-export everything from db.session so cogs can just `import db` as before.
from db.session import (
    init_db, save_chat, get_history, clear_history,
    get_guild_config, set_enabled_channels, set_system_prompt,
    set_aemeath_channels, set_aemeath_interval, get_aemeath_configs,
    add_aemeath_gif, get_all_aemeath_gifs
)

__all__ = [
    "init_db", "save_chat", "get_history", "clear_history",
    "get_guild_config", "set_enabled_channels", "set_system_prompt",
    "set_aemeath_channels", "set_aemeath_interval", "get_aemeath_configs",
    "add_aemeath_gif", "get_all_aemeath_gifs"
]
