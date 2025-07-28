import asyncio
import os
from datetime import datetime

import discord

from .logger import get_logger

logger = get_logger('scheduler')

class ScheduleRunner:
    def __init__(self, bot):
        self.bot = bot
        self._task = None
        logger.info("Scheduler initialized")

    async def start(self):
        if self._task is None:
            logger.info("Starting scheduler task")
            self._task = self.bot.loop.create_task(self._run())
        else:
            logger.debug("Scheduler task already running")

    async def stop(self):
        if self._task is not None:
            logger.info("Stopping scheduler task")
            self._task.cancel()
            self._task = None
        else:
            logger.debug("No scheduler task to stop")

    async def _run(self):
        from .storage import schedule_manager
        
        await self.bot.wait_until_ready()
        
        try:
            while not self.bot.is_closed():
                now = datetime.now()
                messages = schedule_manager.messages
                due_messages = [msg for msg in messages if datetime.fromisoformat(msg["timestamp"]) <= now]
                
                if due_messages:
                    logger.info(f"Processing {len(due_messages)} due messages")
                else:
                    logger.debug("No messages due for delivery")
                
                for msg in due_messages:
                    try:
                        logger.debug(f"Processing message scheduled for {msg['timestamp']}")
                        successful_channels = []
                        failed_channels = []

                        for channel_id in msg["channel_ids"]:
                            channel = self.bot.get_channel(channel_id)
                            if not isinstance(channel, discord.TextChannel):
                                logger.warning(f"Channel {channel_id} is not a text channel")
                                failed_channels.append(f"{channel_id} (invalid channel type)")
                                continue

                            channel_files = []
                            for file_info in msg.get("files", []):
                                try:
                                    file = discord.File(file_info["path"], filename=file_info["filename"])
                                    channel_files.append(file)
                                except Exception as e:
                                    logger.error(f"Error loading file {file_info['path']}: {e}", exc_info=True)
                                    continue
                            
                            content = f"**Scheduled message from {msg['sender_name']}:**\n{msg['content']}" if msg['content'] else f"**Scheduled attachment from {msg['sender_name']}**"
                            try:
                                await channel.send(content=content, files=channel_files)
                                successful_channels.append(str(channel_id))
                            except discord.Forbidden:
                                logger.warning(f"No permission to send message in channel {channel_id}")
                                failed_channels.append(f"{channel_id} (no permission)")
                            except Exception as e:
                                logger.error(f"Error sending message to channel {channel_id}: {e}", exc_info=True)
                                failed_channels.append(f"{channel_id} (error: {str(e)})")

                        # Clean up files
                        for file_info in msg.get("files", []):
                            try:
                                os.remove(file_info["path"])
                                logger.debug(f"Cleaned up file: {file_info['path']}")
                            except Exception as e:
                                logger.error(f"Error removing file {file_info['path']}: {e}", exc_info=True)

                        # Log delivery results
                        if successful_channels:
                            logger.info(f"Message delivered to channels: {', '.join(successful_channels)}")
                        if failed_channels:
                            logger.warning(f"Message delivery failed for channels: {', '.join(failed_channels)}")

                        schedule_manager.remove_message(msg)
                        logger.info("Message removed from schedule")
                    
                    except Exception as e:
                        logger.error(f"Error processing scheduled message: {e}", exc_info=True)

                await asyncio.sleep(60)
        
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled")
            return
        except Exception as e:
            logger.error(f"Schedule runner encountered an error: {e}", exc_info=True)
            self._task = None
            logger.info("Attempting to restart scheduler task")
            await self.start()
