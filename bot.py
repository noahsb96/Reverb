import discord
from discord.ext import commands
from discord.ui import View, Select
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

ALLOWED_USERS = [381173231069036544]

CHANNELS = {
    'general': 1397412820383043667,
    'test': 1397442719202410517,
    'test2': 1397442739838128159,
    'test3': 1397442760738607164,
}
class ChannelSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=name, value=str(chan_id))
            for name, chan_id in CHANNELS.items()
        ]
        super().__init__(placeholder='Select a channel to post in', min_values=1, max_values=len(options), options=options)
        
    async def callback(self, interaction: discord.Interaction):
        self.view.selected_channels = [int(v) for v in self.values]
        await interaction.response.send_message(f'Posting in channels: {", ".join(self.values)}', ephemeral=True)
        self.view.stop()

class ChannelView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.selected_channels = []
        self.add_item(ChannelSelect())

@bot.command(name='postmessage')
async def post_message(ctx):
    if ctx.author.id not in ALLOWED_USERS:
        await ctx.send("You are not allowed to use this command.")
        return

    view = ChannelView()
    await ctx.send("Select channels to post in:", view=view)

    await view.wait()

    if not view.selected_channels:
        await ctx.send("No channels selected or command timed out.")
        return
    
    await ctx.send("Please enter the message you want to post:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    try:
        msg = await bot.wait_for('message', check=check, timeout=120)
    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Please try again.")
        return
    
    content = msg.content
    files = [await a.to_file() for a in msg.attachments]
    
    for channel_id in view.selected_channels:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(content, files=files)

    await ctx.send("Message posted successfully!")

bot.run(TOKEN)