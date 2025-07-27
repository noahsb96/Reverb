import discord
from discord.ui import View

class MessageModalWithAttachment(discord.ui.Modal):
    def __init__(self, selected_channels, attachment):
        super().__init__(title="Message Content")
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

    async def on_submit(self, interaction: discord.Interaction):
        for channel_id in self.selected_channels:
            channel = interaction.guild.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                content = f"**Message from {interaction.user.display_name}:**\n{self.message_input.value}" if self.message_input.value else f"**Attachment from {interaction.user.display_name}**"
                file = await self.attachment.to_file() if self.attachment else None
                await channel.send(
                    content=content,
                    files=[file] if file else None
                )
        await interaction.response.send_message("✅ Message posted successfully!", ephemeral=True)

class ScheduleModalWithAttachment(discord.ui.Modal):
    def __init__(self, selected_channels, attachment):
        super().__init__(title="Schedule Message")
        self.selected_channels = selected_channels
        self.attachment = attachment
        self.message_input = discord.ui.TextInput(
            label="Message (optional)",
            style=discord.TextStyle.paragraph,
            placeholder="Type your message here...",
            required=False,
            max_length=2000
        )
        self.time_input = discord.ui.TextInput(
            label="Time (MM/DD/YYYY HH:MM AM/PM)",
            style=discord.TextStyle.short,
            placeholder="e.g., 07/23/2025 05:30 PM",
            required=True
        )
        self.add_item(self.message_input)
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        from datetime import datetime
        from utils.storage import add_scheduled_message
        import os

        try:
            scheduled_time = datetime.strptime(self.time_input.value.strip(), "%m/%d/%Y %I:%M %p")
        except ValueError:
            await interaction.response.send_message("❌ Invalid time format. Please use MM/DD/YYYY HH:MM AM/PM format.", ephemeral=True)
            return

        current_time = datetime.now()
        
        if scheduled_time < current_time:
            await interaction.response.send_message("⏳ You can't schedule something in the past.", ephemeral=True)
            return

        saved_file = None
        if self.attachment:
            temp_dir = "temp_files"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, f"{interaction.id}_{self.attachment.filename}")
            await self.attachment.save(file_path)
            saved_file = {
                "path": file_path,
                "filename": self.attachment.filename
            }

        message = {
            "channel_ids": self.selected_channels,
            "content": self.message_input.value or None,
            "files": [saved_file] if saved_file else [],
            "timestamp": scheduled_time.isoformat(),
            "sender_name": interaction.user.display_name
        }
        add_scheduled_message(message)
        await interaction.response.send_message(
            f"✅ Message scheduled for {scheduled_time.strftime('%m/%d/%Y %I:%M %p')}", 
            ephemeral=True
        )

class UpdatedChannelSelect(discord.ui.Select):
    def __init__(self, options, attachment, is_schedule=False):
        select_options = [discord.SelectOption(label=name, value=str(cid)) for name, cid in options.items()]
        super().__init__(
            placeholder="Select channels to post in...", 
            min_values=1, 
            max_values=len(select_options), 
            options=select_options
        )
        self.attachment = attachment
        self.is_schedule = is_schedule

    async def callback(self, interaction: discord.Interaction):
        selected_channels = [int(v) for v in self.values]
        modal = ScheduleModalWithAttachment(selected_channels, self.attachment) if self.is_schedule else MessageModalWithAttachment(selected_channels, self.attachment)
        await interaction.response.send_modal(modal)
        self.view.stop()

class UpdatedChannelView(View):
    def __init__(self, options, attachment, is_schedule=False):
        super().__init__(timeout=60)
        self.add_item(UpdatedChannelSelect(options, attachment, is_schedule))
