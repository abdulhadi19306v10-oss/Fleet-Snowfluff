import discord
from discord import app_commands

MASTER_USER_ID = 722706639257600030

def is_admin_or_master(user: discord.Member | discord.User) -> bool:
    if user.id == MASTER_USER_ID:
        return True
    if isinstance(user, discord.Member):
        return user.guild_permissions.administrator or user.guild_permissions.manage_guild or user.guild_permissions.manage_messages
    return False

def admin_or_master():
    """Allows Server Administrators, Mods, OR the global Master User."""
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id == MASTER_USER_ID:
            return True
        perms = interaction.permissions
        return perms.administrator or perms.manage_guild or perms.manage_messages
    return app_commands.check(predicate)
