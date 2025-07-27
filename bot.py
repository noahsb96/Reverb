import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from discord.ui import View, Select
from dotenv import load_dotenv
import json
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

SCHEDULED_FILE = "scheduled.json"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    bot.loop.create_task(schedule_runner())

def load_scheduled_messages():
    if not os.path.exists(SCHEDULED_FILE):
        return []
    with open(SCHEDULED_FILE, 'r') as f:
        return json.load(f)
    
def save_scheduled_messages(scheduled):
    with open(SCHEDULED_FILE, 'w') as f:
        json.dump(scheduled, f, indent=2)

scheduled_messages = load_scheduled_messages()

@bot.tree.command(name="postmessage", description="Post a message to selected channels")
@discord.app_commands.describe(
    attachment="Optional: Add a file, image, or other attachment to your message"
)
async def post_message(interaction: discord.Interaction, attachment: discord.Attachment = None):
    allowed_channels = {
        channel.name: channel.id
        for channel in interaction.guild.channels
        if isinstance(channel, discord.TextChannel) and channel.permissions_for(interaction.user).send_messages
    }

    if not allowed_channels:
        await interaction.response.send_message("⚠️ You don't have permission to post in any configured channels.", ephemeral=True)
        return
    
    attachment_file = await attachment.to_file() if attachment else None
    
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
                    file = await self.attachment.to_file() if self.attachment else None
                    content = f"**Message from {interaction.user.display_name}:**\n{self.message_input.value}" if self.message_input.value else f"**Attachment from {interaction.user.display_name}**"
                    await channel.send(
                        content=content,
                        files=[file] if file else None
                    )
            await interaction.response.send_message("✅ Message posted successfully!", ephemeral=True)

    class UpdatedChannelSelect(discord.ui.Select):
        def __init__(self, options, attachment):
            select_options = [discord.SelectOption(label=name, value=str(cid)) for name, cid in options.items()]
            super().__init__(
                placeholder="Select channels to post in...", 
                min_values=1, 
                max_values=len(select_options), 
                options=select_options
            )
            self.attachment = attachment

        async def callback(self, interaction: discord.Interaction):
            selected_channels = [int(v) for v in self.values]
            modal = MessageModalWithAttachment(selected_channels, self.attachment)
            await interaction.response.send_modal(modal)
            self.view.stop()

    class UpdatedChannelView(discord.ui.View):
        def __init__(self, options, attachment):
            super().__init__(timeout=60)
            self.add_item(UpdatedChannelSelect(options, attachment))

    view = UpdatedChannelView(allowed_channels, attachment)
    await interaction.response.send_message("Select channels to post in:", view=view, ephemeral=True)

@bot.tree.command(name="schedulemessage", description="Schedule a message to post later")
@discord.app_commands.describe(
    attachment="Optional: Add a file, image, or other attachment to your message"
)
async def schedule_message(interaction: discord.Interaction, attachment: discord.Attachment = None):
    allowed_channels = {
        channel.name: channel.id
        for channel in interaction.guild.channels
        if isinstance(channel, discord.TextChannel) and channel.permissions_for(interaction.user).send_messages
    }

    if not allowed_channels:
        await interaction.response.send_message("⚠️ You don't have permission to post in any configured channels.", ephemeral=True)
        return

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
            try:
                scheduled_time = datetime.strptime(self.time_input.value.strip(), "%m/%d/%Y %I:%M %p")
            except ValueError:
                await interaction.response.send_message("❌ Invalid time format. Please use MM/DD/YYYY HH:MM AM/PM format.", ephemeral=True)
                return

            if scheduled_time < datetime.now():
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

            scheduled_messages.append({
                "channel_ids": self.selected_channels,
                "content": self.message_input.value or None,
                "files": [saved_file] if saved_file else [],
                "timestamp": scheduled_time.isoformat(),
                "sender_name": interaction.user.display_name
            })

            save_scheduled_messages(scheduled_messages)
            await interaction.response.send_message(
                f"✅ Message scheduled for {scheduled_time.strftime('%m/%d/%Y %I:%M %p')}", 
                ephemeral=True
            )

    class UpdatedScheduleChannelSelect(discord.ui.Select):
        def __init__(self, options, attachment):
            select_options = [discord.SelectOption(label=name, value=str(cid)) for name, cid in options.items()]
            super().__init__(
                placeholder="Select channels to post in...", 
                min_values=1, 
                max_values=len(select_options), 
                options=select_options
            )
            self.attachment = attachment

        async def callback(self, interaction: discord.Interaction):
            selected_channels = [int(v) for v in self.values]
            modal = ScheduleModalWithAttachment(selected_channels, self.attachment)
            await interaction.response.send_modal(modal)
            self.view.stop()

    class UpdatedScheduleChannelView(discord.ui.View):
        def __init__(self, options, attachment):
            super().__init__(timeout=60)
            self.add_item(UpdatedScheduleChannelSelect(options, attachment))

    view = UpdatedScheduleChannelView(allowed_channels, attachment)
    await interaction.response.send_message("Select channels to schedule a post in:", view=view, ephemeral=True)

@bot.tree.command(name="help", description="List all available commands and how to use them")
async def help_command(interaction: discord.Interaction):
    help_embed = discord.Embed(
        title="Reverb Bot Commands",
        description="Here's a list of all available commands and how to use them:",
        color=discord.Color.blue()
    )
    
    help_embed.add_field(
        name="/postmessage",
        value=(
            "Post a message to multiple channels at once.\n"
            "• Optional: Attach a file when using the command\n"
            "• Select which channels to post to\n"
            "• Add your message text (optional)\n"
            "The message will show who sent it."
        ),
        inline=False
    )
    
    help_embed.add_field(
        name="/schedulemessage",
        value=(
            "Schedule a message to be posted later.\n"
            "• Optional: Attach a file when using the command\n"
            "• Select which channels to post to\n"
            "• Add your message text (optional)\n"
            "• Set the date and time (format: MM/DD/YYYY HH:MM AM/PM)\n"
            "The message will show who scheduled it when it's posted."
        ),
        inline=False
    )
    
    help_embed.add_field(
        name="/help",
        value="Show this help message with all available commands.",
        inline=False
    )

    help_embed.set_footer(text="All interactions with the bot are private - other users won't see you using the commands.")
    
    await interaction.response.send_message(embed=help_embed, ephemeral=True)

async def schedule_runner():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        to_post = [msg for msg in scheduled_messages if datetime.fromisoformat(msg["timestamp"]) <= now]

        for msg in to_post:
            files = []
            for file_info in msg.get("files", []):
                try:
                    file = discord.File(file_info["path"], filename=file_info["filename"])
                    files.append(file)
                except Exception as e:
                    print(f"Error loading file {file_info['path']}: {e}")

            for channel_id in msg["channel_ids"]:
                channel = bot.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    try:
                        content = f"**Scheduled message from {msg['sender_name']}:**\n{msg['content']}" if msg['content'] else f"**Scheduled attachment from {msg['sender_name']}**"
                        await channel.send(content=content, files=files)
                    except Exception as e:
                        print(f"Error sending message to channel {channel_id}: {e}")

            for file_info in msg.get("files", []):
                try:
                    os.remove(file_info["path"])
                except Exception as e:
                    print(f"Error removing file {file_info['path']}: {e}")

            scheduled_messages.remove(msg)
            save_scheduled_messages(scheduled_messages)

        await asyncio.sleep(60)

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN environment variable is not set")
bot.run(TOKEN)
