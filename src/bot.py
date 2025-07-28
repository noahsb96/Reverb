"""Main bot module for Reverb."""

import asyncio
import os
from datetime import datetime
from typing import List

import discord
from discord.ext import commands
from dotenv import load_dotenv

from .utils.scheduler import ScheduleRunner


class ReverbBot(commands.Bot):
    """Main bot class for Reverb."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        
        super().__init__(command_prefix='!', intents=intents)
        self.initial_extensions = ['message', 'schedule', 'help']
        self.scheduler = ScheduleRunner(self)

    async def setup_hook(self) -> None:
        """Initialize the bot's extensions and sync commands."""
        for ext in self.initial_extensions:
            try:
                await self.load_extension(f"src.cogs.{ext}")
                print(f"Loaded extension: {ext}")
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")

        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Error syncing commands: {e}")

        await self.scheduler.start()

    async def on_ready(self):
        """Called when the bot is ready to start."""
        print(f"{self.user} is ready!")


def run_bot():
    """Initialize and run the bot."""
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if TOKEN is None:
        raise ValueError("DISCORD_TOKEN environment variable is not set")
    
    bot = ReverbBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    run_bot()
