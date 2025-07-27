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

CHANNELS = {
    'general': 1397412820383043667,
    'test': 1397442719202410517,
    'test2': 1397442739838128159,
    'test3': 1397442760738607164,
}

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

class ChannelSelect(Select):
    def __init__(self, options, is_schedule=False):
        select_options = [discord.SelectOption(label=name, value=str(cid)) for name, cid in options.items()]
        super().__init__(placeholder="Select channels to post in...", min_values=1, max_values=len(select_options), options=select_options)
        self.is_schedule = is_schedule

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view and isinstance(view, ChannelView):
            selected_channels = [int(v) for v in self.values]
            modal = ScheduleMessageModal(selected_channels) if self.is_schedule else MessageModal(selected_channels)
            await interaction.response.send_modal(modal)
            view.stop()

class MessageModal(discord.ui.Modal):
    def __init__(self, selected_channels):
        super().__init__(title="Message Content")
        self.selected_channels = selected_channels
        self.message_input = discord.ui.TextInput(
            label="Message",
            style=discord.TextStyle.paragraph,
            placeholder="Type your message here...",
            required=True,
            max_length=2000
        )
        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        for channel_id in self.selected_channels:
            channel = interaction.guild.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                await channel.send(self.message_input.value)
        await interaction.response.send_message("✅ Message posted successfully!", ephemeral=True)

class ScheduleMessageModal(discord.ui.Modal):
    def __init__(self, selected_channels):
        super().__init__(title="Schedule Message")
        self.selected_channels = selected_channels
        self.message_input = discord.ui.TextInput(
            label="Message",
            style=discord.TextStyle.paragraph,
            placeholder="Type your message here...",
            required=True,
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

        scheduled_messages.append({
            "channel_ids": self.selected_channels,
            "content": self.message_input.value,
            "files": [],
            "timestamp": scheduled_time.isoformat()
        })

        save_scheduled_messages(scheduled_messages)
        await interaction.response.send_message(
            f"✅ Message scheduled for {scheduled_time.strftime('%m/%d/%Y %I:%M %p')}", 
            ephemeral=True
        )

class ChannelView(View):
    def __init__(self, options, is_schedule=False):
        super().__init__(timeout=60)
        self.add_item(ChannelSelect(options, is_schedule))

@bot.tree.command(name="postmessage", description="Post a message to selected channels")
async def post_message(interaction: discord.Interaction):
    allowed_channels = {
        name: cid for name, cid in CHANNELS.items()
        if isinstance((channel := interaction.guild.get_channel(cid)), discord.TextChannel) and channel.permissions_for(interaction.user).send_messages
    }

    if not allowed_channels:
        await interaction.response.send_message("⚠️ You don't have permission to post in any configured channels.", ephemeral=True)
        return

    view = ChannelView(allowed_channels, is_schedule=False)
    await interaction.response.send_message("Select channels to post in:", view=view, ephemeral=True)

@bot.tree.command(name="schedulemessage", description="Schedule a message to post later")
async def schedule_message(interaction: discord.Interaction):
    allowed_channels = {
        name: cid for name, cid in CHANNELS.items()
        if isinstance((channel := interaction.guild.get_channel(cid)), discord.TextChannel) and channel.permissions_for(interaction.user).send_messages
    }

    if not allowed_channels:
        await interaction.response.send_message("⚠️ You don't have permission to post in any configured channels.", ephemeral=True)
        return

    view = ChannelView(allowed_channels, is_schedule=True)
    await interaction.response.send_message("Select channels to schedule a post in:", view=view, ephemeral=True)

async def schedule_runner():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        to_post = [msg for msg in scheduled_messages if datetime.fromisoformat(msg["timestamp"]) <= now]

        for msg in to_post:
            for channel_id in msg["channel_ids"]:
                channel = bot.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    await channel.send(msg["content"])
            scheduled_messages.remove(msg)
            save_scheduled_messages(scheduled_messages)

        await asyncio.sleep(60)

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN environment variable is not set")
bot.run(TOKEN)
