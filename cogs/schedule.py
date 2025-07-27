import discord
from discord import app_commands
from discord.ext import commands
from .views import UpdatedChannelView

class ScheduleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="schedulemessage", description="Schedule a message to post later")
    @app_commands.describe(
        attachment="Optional: Add a file, image, or other attachment to your message"
    )
    async def schedule_message(self, interaction: discord.Interaction, attachment: discord.Attachment = None):
        allowed_channels = {
            channel.name: channel.id
            for channel in interaction.guild.channels
            if isinstance(channel, discord.TextChannel) and channel.permissions_for(interaction.user).send_messages
        }

        if not allowed_channels:
            await interaction.response.send_message("⚠️ You don't have permission to post in any configured channels.", ephemeral=True)
            return

        view = UpdatedChannelView(allowed_channels, attachment, is_schedule=True)
        await interaction.response.send_message("Select channels to schedule a post in:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ScheduleCommands(bot))
