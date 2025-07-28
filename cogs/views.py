import discord
from discord.ui import View, Select
from typing import Dict, List

class ChannelSearchModal(discord.ui.Modal):
    def __init__(self, channel_view: 'UpdatedChannelView'):
        super().__init__(title="Search Channels")
        self.channel_view = channel_view
        self.search_input = discord.ui.TextInput(
            label="Search channels",
            placeholder="Type to filter channels...",
            required=True,
            max_length=100
        )
        self.add_item(self.search_input)

    async def on_submit(self, interaction: discord.Interaction):
        search_term = self.search_input.value.lower()
        self.channel_view.update_channel_list(search_term)
        await interaction.response.edit_message(view=self.channel_view)

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
                    content = f"**Message from {interaction.user.display_name}:**\n{self.message_input.value}" if self.message_input.value else f"**Attachment from {interaction.user.display_name}**"
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
            
            if success_channels and not failed_channels:
                await interaction.followup.send("✅ Message posted successfully to all channels!", ephemeral=True)
            elif success_channels and failed_channels:
                message = "✅ Message posted to: " + ", ".join(success_channels) + "\n"
                message += "❌ Failed to post to: " + ", ".join(failed_channels)
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to post message to any channels: " + ", ".join(failed_channels), ephemeral=True)
                
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)
            except:
                print(f"Error in MessageModalWithAttachment: {str(e)}")

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
            await interaction.response.defer(ephemeral=True)
            
            try:
                scheduled_time = datetime.strptime(self.time_input.value.strip(), "%m/%d/%Y %I:%M %p")
            except ValueError:
                await interaction.followup.send("❌ Invalid time format. Please use MM/DD/YYYY HH:MM AM/PM format.", ephemeral=True)
                return

            current_time = datetime.now()
            if scheduled_time < current_time:
                await interaction.followup.send("⏳ You can't schedule something in the past.", ephemeral=True)
                return

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
            
            if not valid_channels:
                await interaction.followup.send(
                    f"❌ Cannot schedule message: No valid channels with proper permissions.\nFailed channels: {', '.join(invalid_channels)}", 
                    ephemeral=True
                )
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
                print(f"Error in ScheduleModalWithAttachment: {str(e)}")

class UpdatedChannelSelect(discord.ui.Select):
    def __init__(self, options: Dict[str, int], attachment, is_schedule: bool):
        select_options = [
            discord.SelectOption(
                label=name[:25],
                value=str(cid),
                default=False
            )
            for name, cid in options.items()
        ]
        
        super().__init__(
            placeholder="Select channels to post in...",
            min_values=1,
            max_values=len(select_options),
            options=select_options
        )
        self.attachment = attachment
        self.is_schedule = is_schedule
        self.all_options = options

    async def callback(self, interaction: discord.Interaction):
        selected_channels = [int(v) for v in self.values]
        modal = ScheduleModalWithAttachment(selected_channels, self.attachment) if self.is_schedule else MessageModalWithAttachment(selected_channels, self.attachment)
        await interaction.response.send_modal(modal)

class UpdatedChannelView(View):
    def __init__(self, options: Dict[str, int], attachment, is_schedule: bool = False):
        super().__init__(timeout=180)
        self.all_options = options
        self.attachment = attachment
        self.is_schedule = is_schedule
        self.update_channel_list()
        
        self.add_item(discord.ui.Button(
            label="🔍 Search Channels",
            style=discord.ButtonStyle.secondary,
            custom_id="search",
            row=0
        ))
        self.add_item(discord.ui.Button(
            label="Clear Search",
            style=discord.ButtonStyle.secondary,
            custom_id="clear",
            row=0
        ))

    def update_channel_list(self, search_term: str = ""):
        for item in self.children[:]:
            if isinstance(item, UpdatedChannelSelect):
                self.remove_item(item)

        filtered_options = {
            name: cid
            for name, cid in self.all_options.items()
            if search_term.lower() in name.lower()
        }

        if filtered_options:
            select_menu = UpdatedChannelSelect(filtered_options, self.attachment, self.is_schedule)
            select_menu.row = 1
            self.add_item(select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "search":
            await interaction.response.send_modal(ChannelSearchModal(self))
        elif interaction.data["custom_id"] == "clear":
            self.update_channel_list()
            await interaction.response.edit_message(view=self)
        return True


