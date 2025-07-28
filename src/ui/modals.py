"""Modal dialogs for the bot's UI."""

from datetime import datetime
from typing import List

import discord

from ..utils.storage import add_scheduled_message
from .base import BaseMessageModal, SaveFileContext

class MessageModal(BaseMessageModal):
    """Modal for sending immediate messages."""

    def __init__(self, selected_channels: List[int], attachment: discord.Attachment):
        super().__init__(selected_channels, attachment, title="Message Content")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            success_channels = []
            failed_channels = []
            
            for channel_id in self.selected_channels:
                channel = interaction.guild.get_channel(channel_id)
                if not isinstance(channel, discord.TextChannel):
                    failed_channels.append(f"{channel.name} (invalid channel type)")
                    continue
                    
                if not channel.permissions_for(interaction.user).send_messages:
                    failed_channels.append(f"{channel.name} (no permission)")
                    continue
                
                try:
                    content = self._format_content(interaction.user.display_name)
                    file = await self.attachment.to_file() if self.attachment else None
                    await channel.send(
                        content=content,
                        files=[file] if file else None
                    )
                    success_channels.append(channel.name)
                except discord.Forbidden:
                    failed_channels.append(f"{channel.name} (no permission)")
                except Exception as e:
                    failed_channels.append(f"{channel.name} (error: {str(e)})")
            
            await self._handle_response(interaction, success_channels, failed_channels)
                
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)
            except:
                print(f"Error in MessageModal: {str(e)}")


class ScheduleModal(BaseMessageModal):
    """Modal for scheduling messages."""

    def __init__(self, selected_channels: List[int], attachment: discord.Attachment):
        super().__init__(selected_channels, attachment, title="Schedule Message")
        self.time_input = discord.ui.TextInput(
            label="Time (MM/DD/YYYY HH:MM AM/PM)",
            style=discord.TextStyle.short,
            placeholder="e.g., 07/23/2025 05:30 PM",
            required=True
        )
        self.add_item(self.time_input)

    async def _validate_time(self, interaction: discord.Interaction) -> datetime | None:
        """Validate the scheduled time input."""
        try:
            scheduled_time = datetime.strptime(self.time_input.value.strip(), "%m/%d/%Y %I:%M %p")
        except ValueError:
            await interaction.followup.send(
                "❌ Invalid time format. Please use MM/DD/YYYY HH:MM AM/PM format.", 
                ephemeral=True
            )
            return None

        if scheduled_time < datetime.now():
            await interaction.followup.send("⏳ You can't schedule something in the past.", ephemeral=True)
            return None

        return scheduled_time

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            scheduled_time = await self._validate_time(interaction)
            if not scheduled_time:
                return

            valid_channels, invalid_channels = await self._validate_channels(interaction)
            
            if not valid_channels:
                await interaction.followup.send(
                    f"❌ Cannot schedule message: No valid channels with proper permissions.\nFailed channels: {', '.join(invalid_channels)}", 
                    ephemeral=True
                )
                return

            async with SaveFileContext(self.attachment, interaction.id) as saved_file:
                message = {
                    "channel_ids": valid_channels,
                    "content": self.message_input.value or None,
                    "files": [saved_file] if saved_file else [],
                    "timestamp": scheduled_time.isoformat(),
                    "sender_name": interaction.user.display_name
                }
                add_scheduled_message(message)
            
            response = f"✅ Message scheduled for {scheduled_time.strftime('%m/%d/%Y %I:%M %p')}"
            if invalid_channels:
                response += f"\n⚠️ Note: Message will not be sent to: {', '.join(invalid_channels)}"
            
            await interaction.followup.send(response, ephemeral=True)
            
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ An error occurred while scheduling the message: {str(e)}", ephemeral=True)
            except:
                print(f"Error in ScheduleModal: {str(e)}")

