import discord
from discord import app_commands
from discord.ext import commands
from ..ui.views import ChannelView

from .base import BaseCog

class ScheduleCommands(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @app_commands.command(name="schedulemessage", description="Schedule a message to post later")
    @app_commands.describe(
        attachment="Optional: Add a file, image, or other attachment to your message"
    )
    async def schedule_message(self, interaction: discord.Interaction, attachment: discord.Attachment = None):
        allowed_channels = self._get_allowed_channels(interaction)
        if not allowed_channels:
            await interaction.response.send_message(
                "⚠️ You don't have permission to post in any configured channels.",
                ephemeral=True
            )
            return

        view = ChannelView(allowed_channels, attachment, is_schedule=True)
        await interaction.response.send_message(
            "Select channels to schedule a post in (you can select multiple):",
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ScheduleCommands(bot))
