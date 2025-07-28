import discord
from discord import app_commands
from discord.ext import commands
from .views import UpdatedChannelView

class MessageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._channel_cache = {}

    def _get_allowed_channels(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id not in self._channel_cache:
            self._channel_cache[guild_id] = {
                channel.name: channel.id
                for channel in interaction.guild.channels
                if isinstance(channel, discord.TextChannel) and 
                channel.permissions_for(interaction.user).send_messages
            }
        return self._channel_cache[guild_id]

    @app_commands.command(name="postmessage", description="Post a message to selected channels")
    @app_commands.describe(
        attachment="Optional: Add a file, image, or other attachment to your message"
    )
    async def post_message(self, interaction: discord.Interaction, attachment: discord.Attachment = None):
        allowed_channels = self._get_allowed_channels(interaction)
        if not allowed_channels:
            await interaction.response.send_message(
                "⚠️ You don't have permission to post in any configured channels.",
                ephemeral=True
            )
            return

        view = UpdatedChannelView(allowed_channels, attachment, is_schedule=False)
        await interaction.response.send_message(
            "Select channels to post in (you can select multiple):",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(MessageCommands(bot))
