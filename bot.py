import asyncio
from datetime import datetime
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.storage import load_scheduled_messages, save_scheduled_messages, scheduled_messages, remove_scheduled_message

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Load scheduled messages at startup
load_scheduled_messages()

# Load cogs at startup
async def setup_bot():
    cog_extensions = ['message', 'schedule', 'help']  # List of cog modules to load
    for cog in cog_extensions:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"Loaded extension: {cog}")
        except Exception as e:
            print(f"Failed to load extension {cog}: {e}")

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    try:
        await setup_bot()  # Load cogs first
        synced = await bot.tree.sync()  # Then sync commands
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error during setup: {e}")

    bot.loop.create_task(schedule_runner())

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

            remove_scheduled_message(msg)

        await asyncio.sleep(60)

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN environment variable is not set")

bot.run(TOKEN)
