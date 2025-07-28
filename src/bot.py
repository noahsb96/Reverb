"""Main bot module for Reverb."""

import asyncio
import os
from datetime import datetime
from typing import List

import discord
from discord.ext import commands
from dotenv import load_dotenv

from .utils.logger import setup_logger, get_logger
from .utils.scheduler import ScheduleRunner

logger = get_logger('bot')


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
        logger.info("Setting up bot extensions and commands")
        
        for ext in self.initial_extensions:
            try:
                await self.load_extension(f"src.cogs.{ext}")
                logger.info(f"Loaded extension: {ext}")
            except Exception as e:
                logger.error(f"Failed to load extension {ext}: {e}", exc_info=True)

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}", exc_info=True)

        logger.info("Starting scheduler")
        await self.scheduler.start()

    async def on_ready(self):
        """Called when the bot is ready to start."""
        logger.info(f"Bot {self.user} is ready!")
        
        # Log some bot statistics
        guild_count = len(self.guilds)
        channel_count = sum(len(guild.channels) for guild in self.guilds)
        logger.info(f"Connected to {guild_count} guilds with {channel_count} channels total")


def run_bot():
    """Initialize and run the bot."""
    load_dotenv()
    
    # Initialize logging
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    setup_logger(debug_mode)
    
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN is None:
        logger.error("DISCORD_TOKEN environment variable is not set")
        raise ValueError("DISCORD_TOKEN environment variable is not set")
    
    try:
        logger.info("Initializing bot")
        bot = ReverbBot()
        logger.info("Starting bot")
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_bot()
