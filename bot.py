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
    def __init__(self, options):
        select_options = [discord.SelectOption(label=name, value=str(cid)) for name, cid in options.items()]
        super().__init__(placeholder="Select channels to post in...", min_values=1, max_values=len(select_options), options=select_options)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view and isinstance(view, ChannelView):
            view.selected_channels = [int(v) for v in self.values]
            await interaction.response.send_message("✅ Channels selected!", ephemeral=True)
            view.stop()

class ChannelView(View):
    def __init__(self, options):
        super().__init__(timeout=60)
        self.selected_channels = []
        self.add_item(ChannelSelect(options))

@bot.tree.command(name="postmessage", description="Post a message to selected channels")
async def post_message(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    allowed_channels = {
        name: cid for name, cid in CHANNELS.items()
        if isinstance((channel := interaction.guild.get_channel(cid)), discord.TextChannel) and channel.permissions_for(interaction.user).send_messages
    }

    if not allowed_channels:
        await interaction.followup.send("⚠️ You don’t have permission to post in any configured channels.", ephemeral=True)
        return

    view = ChannelView(allowed_channels)
    await interaction.followup.send("Select channels to post in:", view=view, ephemeral=True)
    timeout = await view.wait()

    if not view.selected_channels:
        await interaction.followup.send("❌ No channels selected or command timed out.", ephemeral=True)
        return

    await interaction.followup.send("Please type the message you want to post:", ephemeral=True)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
        try:
            await msg.delete()
        except discord.Forbidden:
            await interaction.followup.send("⚠️ I couldn't delete your message — please check my permissions.", ephemeral=True)
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ You took too long to respond.", ephemeral=True)
        return

    for channel_id in view.selected_channels:
        channel = interaction.guild.get_channel(channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(msg.content, files=[await a.to_file() for a in msg.attachments])

    await interaction.followup.send("✅ Message posted successfully!", ephemeral=True)

@bot.tree.command(name="schedulemessage", description="Schedule a message to post later")
async def schedule_message(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    allowed_channels = {
        name: cid for name, cid in CHANNELS.items()
        if isinstance((channel := interaction.guild.get_channel(cid)), discord.TextChannel) and channel.permissions_for(interaction.user).send_messages
    }

    if not allowed_channels:
        await interaction.followup.send("⚠️ You don’t have permission to post in any configured channels.", ephemeral=True)
        return

    view = ChannelView(allowed_channels)
    await interaction.followup.send("Select channels to schedule a post in:", view=view, ephemeral=True)
    timeout = await view.wait()

    if not view.selected_channels:
        await interaction.followup.send("❌ No channels selected or command timed out.", ephemeral=True)
        return

    await interaction.followup.send("Please type the message you want to schedule:", ephemeral=True)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
        try:
            await msg.delete()
        except discord.Forbidden:
            await interaction.followup.send("⚠️ I couldn't delete your message — please check my permissions.", ephemeral=True)
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ You took too long to respond.", ephemeral=True)
        return

    await interaction.followup.send("Enter the scheduled time in format `MM/DD/YYYY HH:MM AM/PM` (e.g. `07/23/2025 05:30 PM`):", ephemeral=True)

    try:
        time_msg = await bot.wait_for("message", check=check, timeout=60)
        scheduled_time = datetime.strptime(time_msg.content.strip(), "%m/%d/%Y %I:%M %p")
        await time_msg.delete()
    except (asyncio.TimeoutError, ValueError):
        await interaction.followup.send("❌ Invalid time format. Please use `MM/DD/YYYY HH:MM AM/PM`, e.g., `07/23/2025 03:45 PM`.", ephemeral=True)
        return

    if scheduled_time < datetime.now():
        await interaction.followup.send("⏳ You can't schedule something in the past.", ephemeral=True)
        return

    scheduled_messages.append({
        "channel_ids": view.selected_channels,
        "content": msg.content,
        "files": [],
        "timestamp": scheduled_time.isoformat()
    })

    save_scheduled_messages(scheduled_messages)
    await interaction.followup.send(f"✅ Message scheduled for {scheduled_time.strftime('%m/%d/%Y %I:%M %p')}", ephemeral=True)

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
