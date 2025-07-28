"""Base modal classes for message handling."""

import os
from typing import List

import discord


class BaseMessageModal(discord.ui.Modal):
    """Base class for message modals with common functionality."""
    
    def __init__(self, selected_channels: List[int], attachment: discord.Attachment, title: str):
        super().__init__(title=title)
        self.selected_channels = selected_channels
        self.attachment = attachment
        self.message_input = discord.ui.TextInput(
            label="Message (optional)",
            style=discord.TextStyle.paragraph,
            placeholder="Type your message here...",
            required=False,
            max_length=2000
        )
        self.add_item(self.message_input)

    def _format_content(self, user_name: str) -> str:
        """Format the message content with user name."""
        return (
            f"**Message from {user_name}:**\n{self.message_input.value}" 
            if self.message_input.value 
            else f"**Attachment from {user_name}**"
        )

    async def _validate_channels(
        self, 
        interaction: discord.Interaction
    ) -> tuple[List[int], List[str]]:
        """Validate channels and return valid channel IDs and error messages."""
        valid_channels = []
        invalid_channels = []
        
        for channel_id in self.selected_channels:
            channel = interaction.guild.get_channel(channel_id)
            if not isinstance(channel, discord.TextChannel):
                invalid_channels.append(f"{channel.name} (invalid channel type)")
                continue
                
            if not channel.permissions_for(interaction.user).send_messages:
                invalid_channels.append(f"{channel.name} (no permission)")
                continue
                
            valid_channels.append(channel_id)
        
        return valid_channels, invalid_channels

    async def _handle_response(
        self, 
        interaction: discord.Interaction, 
        success_channels: List[str], 
        failed_channels: List[str]
    ):
        """Handle the response to the user based on success/failure."""
        if success_channels and not failed_channels:
            await interaction.followup.send("✅ Message posted successfully to all channels!", ephemeral=True)
        elif success_channels and failed_channels:
            message = "✅ Message posted to: " + ", ".join(success_channels) + "\n"
            message += "❌ Failed to post to: " + ", ".join(failed_channels)
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to post message to any channels: " + ", ".join(failed_channels), ephemeral=True)


class SaveFileContext:
    """Context manager for saving and cleaning up temporary files."""

    def __init__(self, attachment: discord.Attachment, interaction_id: int):
        self.attachment = attachment
        self.interaction_id = interaction_id
        self.file_info = None

    async def __aenter__(self):
        if self.attachment:
            temp_dir = "temp_files"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, f"{self.interaction_id}_{self.attachment.filename}")
            await self.attachment.save(file_path)
            self.file_info = {
                "path": file_path,
                "filename": self.attachment.filename
            }
        return self.file_info

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self.file_info:
            # Clean up the file if there was an error
            try:
                os.remove(self.file_info["path"])
            except Exception:
                pass
