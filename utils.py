import discord
from discord import app_commands

MASTER_USER_ID = 722706639257600030

def admin_or_master():
    """Allows Server Administrators OR the global Master User."""
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id == MASTER_USER_ID:
            return True
        return interaction.permissions.administrator
    return app_commands.check(predicate)
