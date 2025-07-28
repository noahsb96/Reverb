from discord.ext import commands
import discord
from typing import Dict, List, Optional

class BaseCog(commands.Cog):
    """Base class for all cogs providing common functionality"""
    
    def __init__(self, bot):
        self.bot = bot

    def _get_allowed_channels(self, interaction: discord.Interaction) -> Dict[str, int]:
        """Get channels where the user has permission to post"""
        return {
            channel.name: channel.id
            for channel in interaction.guild.channels
            if isinstance(channel, discord.TextChannel) and 
            channel.permissions_for(interaction.user).send_messages
        }

    async def check_channel_permissions(
        self, 
        channel: discord.TextChannel, 
        permissions: List[discord.Permissions]
    ) -> Optional[str]:
        """Check if the bot has the required permissions in a channel.
        
        Args:
            channel: The channel to check permissions for.
            permissions: List of required permissions.

        Returns:
            str: Error message if permissions are missing, None otherwise.
        """
        if not isinstance(channel, discord.TextChannel):
            return "Invalid channel type. Must be a text channel."

        bot_member = channel.guild.me
        channel_perms = channel.permissions_for(bot_member)

        missing_perms = [
            perm.name for perm in permissions 
            if not getattr(channel_perms, perm.name, False)
        ]

        if missing_perms:
            return (
                f"I need the following permissions in {channel.mention}: " 
                f"{', '.join(missing_perms)}"
            )

        return None
