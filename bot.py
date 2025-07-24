import aiofiles
import asyncio
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord.ui import View, Select
from dotenv import load_dotenv
import json
import os
import pytz 

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

SCHEDULED_FILE = "scheduled.json"
PERMISSIONS_FILE = "permissions.json"
USERS_FILE = "users.json"

CHANNELS = {
    'general': 1397412820383043667,
    'test': 1397442719202410517,
    'test2': 1397442739838128159,
    'test3': 1397442760738607164,
}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

def load_permissions():
    if not os.path.exists(PERMISSIONS_FILE):
        return {"admins": [], "managers": [], "users": {}}
    with open(PERMISSIONS_FILE, 'r') as f:
        return json.load(f)

def save_permissions(data):
    with open(PERMISSIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_allowed_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_allowed_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_scheduled_messages():
    if not os.path.exists(SCHEDULED_FILE):
        return []
    with open(SCHEDULED_FILE, 'r') as f:
        return json.load(f)
    
def save_scheduled_messages(scheduled):
    with open(SCHEDULED_FILE, 'w') as f:
        json.dump(scheduled, f, indent=2)

scheduled_messages = load_scheduled_messages()
permissions = load_permissions()
ALLOWED_USERS = load_allowed_users()

def is_admin(user_id):
    return user_id in permissions.get("admins", [])

def is_manager(user_id):
    return user_id in permissions.get("managers", []) or is_admin(user_id)

def get_user_channels(user_id):
    return permissions.get("users", {}).get(str(user_id), [])

def can_post_in_channel(user_id, channel_id):
    return is_admin(user_id) or channel_id in get_user_channels(user_id)

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

@bot.command(name='adduser')
@commands.has_permissions(administrator=True)
async def add_user(ctx, member: discord.Member):
    if member.id in ALLOWED_USERS:
        await ctx.send(f"{member.mention} is already allowed to use this command.")
        return

    ALLOWED_USERS.append(member.id)
    save_allowed_users(ALLOWED_USERS)
    await ctx.send(f"{member.mention} has been added to the allowed users list.")

@bot.command(name='removeuser')
@commands.has_permissions(administrator=True)
async def remove_user(ctx, member: discord.Member):
    if member.id not in ALLOWED_USERS:
        await ctx.send(f"{member.mention} is not in the allowed users list.")
        return

    ALLOWED_USERS.remove(member.id)
    save_allowed_users(ALLOWED_USERS)
    await ctx.send(f"{member.mention} has been removed from the allowed users list.")

@add_user.error
@remove_user.error
async def user_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")

@bot.command(name='postmessage')
async def post_message(ctx):
    user_id = ctx.author.id
    if not (is_admin(user_id) or user_id in permissions["users"]):
        await ctx.send("❌ You are not allowed to post picks.")
        return

    allowed_channel_ids = list(CHANNELS.values()) if is_admin(user_id) else get_user_channels(user_id)

    if not allowed_channel_ids:
        await ctx.send("⚠️ You don’t have any channels assigned to post in.")
        return

    allowed_channels = {name: cid for name, cid in CHANNELS.items() if cid in allowed_channel_ids}
    if not allowed_channels:
        await ctx.send("⚠️ No matching channels found for your permissions.")
        return

    view = ChannelView(allowed_channels)
    await ctx.send("Select channels to post in:", view=view)
    await view.wait()

    if not view.selected_channels:
        await ctx.send("No channels selected or command timed out.")
        return

    await ctx.send("Please enter the message you want to post:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
    except asyncio.TimeoutError:
        await ctx.send("⏰ You took too long to respond.")
        return

    content = msg.content
    files = [await a.to_file() for a in msg.attachments]

    for channel_id in view.selected_channels:
        channel = bot.get_channel(channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(content, files=files)
        else:
            await ctx.send(f"⚠️ Channel ID {channel_id} is not a text channel and was skipped.")

    await ctx.send("✅ Message posted successfully!")

@bot.command(name='schedulemessage')
async def schedule_message(ctx):
    user_id = ctx.author.id
    if not (is_admin(user_id) or user_id in permissions["users"]):
        await ctx.send("❌ You are not allowed to schedule messages.")
        return

    allowed_channel_ids = list(CHANNELS.values()) if is_admin(user_id) else get_user_channels(user_id)
    if not allowed_channel_ids:
        await ctx.send("⚠️ You don’t have any channels assigned.")
        return

    allowed_channels = {name: cid for name, cid in CHANNELS.items() if cid in allowed_channel_ids}
    if not allowed_channels:
        await ctx.send("⚠️ No matching channels found.")
        return

    view = ChannelView(allowed_channels)
    await ctx.send("Select channels to post in:", view=view)
    await view.wait()

    if not view.selected_channels:
        await ctx.send("No channels selected or timed out.")
        return

    await ctx.send("Please enter the message you want to schedule:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
    except asyncio.TimeoutError:
        await ctx.send("⏰ You took too long to respond.")
        return

    content = msg.content
    files = [await a.to_file() for a in msg.attachments]
    await ctx.send("Enter the scheduled time in format `MM/DD/YYYY HH:MM AM/PM` (e.g. `07/23/2025 05:30 PM`):")

    try:
        time_msg = await bot.wait_for("message", check=check, timeout=60)
        scheduled_time = datetime.strptime(time_msg.content.strip(), "%m/%d/%Y %I:%M %p")
    except (asyncio.TimeoutError, ValueError):
        await ctx.send("❌ Invalid time format. Please use `MM/DD/YYYY HH:MM AM/PM`, e.g., `07/23/2025 03:45 PM`.")
        return

    if scheduled_time < datetime.now():
        await ctx.send("⏳ You can't schedule something in the past.")
        return

    scheduled_messages.append({
        "user_id": user_id,
        "channel_ids": view.selected_channels,
        "content": content,
        "files": [],
        "timestamp": scheduled_time.isoformat()
    })

    save_scheduled_messages(scheduled_messages)
    await ctx.send(f"✅ Message scheduled for {scheduled_time.strftime('%m/%d/%Y %I:%M %p')}")

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    bot.loop.create_task(schedule_runner())

async def schedule_runner():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        to_post = [msg for msg in scheduled_messages if datetime.fromisoformat(msg["timestamp"]) <= now]

        for msg in to_post:
            for channel_id in msg["channel_ids"]:
                channel = bot.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    await channel.send(msg["content"])  # File support can be added here
            scheduled_messages.remove(msg)
            save_scheduled_messages(scheduled_messages)

        await asyncio.sleep(60)

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN environment variable is not set")
bot.run(TOKEN)
