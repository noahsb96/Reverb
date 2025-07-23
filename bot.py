import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)


#List of allowed users (user IDs of cappers)
ALLOWED_USERS = [123456789012345678, 987654321098765432] # Replace with actual user IDs

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.command(name='post_pick')
async def post_pick(ctx, *, message=None):
    if ctx.author.id not in ALLOWED_USERS:
        await ctx.send("You are not allowed to use this command.")
        return

    if not message and not ctx.message.attachments:
        await ctx.send("Please provide a message or image.")
        return
    
    #Get the channel to post in (replace with actual ones)
    CHANNEL_IDS = [
        1111111111111111111,  # General picks channel
        2222222222222222222,  # Capper's personal channel
        3333333333333333333   # Platinum picks channel
    ]

    for channel_id in CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            content = message if message else ""
            files = [await att.to_file() for att in ctx.message.attachments]
            await channel.send(content, files=files)

    await ctx.send("Pick posted successfully!")

bot.run(TOKEN)