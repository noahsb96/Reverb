import asyncio
import discord
from datetime import datetime
import os

class ScheduleRunner:
    def __init__(self, bot):
        self.bot = bot
        self._task = None

    async def start(self):
        if self._task is None:
            self._task = self.bot.loop.create_task(self._run())

    async def stop(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _run(self):
        from .storage import schedule_manager
        
        await self.bot.wait_until_ready()
        
        try:
            while not self.bot.is_closed():
                now = datetime.now()
                messages = schedule_manager.messages
                due_messages = [msg for msg in messages if datetime.fromisoformat(msg["timestamp"]) <= now]
                
                for msg in due_messages:
                    try:
                        for channel_id in msg["channel_ids"]:
                            channel = self.bot.get_channel(channel_id)
                            if isinstance(channel, discord.TextChannel):
                                channel_files = []
                                for file_info in msg.get("files", []):
                                    try:
                                        file = discord.File(file_info["path"], filename=file_info["filename"])
                                        channel_files.append(file)
                                    except Exception as e:
                                        print(f"Error loading file {file_info['path']}: {e}")
                                        continue
                                
                                content = f"**Scheduled message from {msg['sender_name']}:**\n{msg['content']}" if msg['content'] else f"**Scheduled attachment from {msg['sender_name']}**"
                                await channel.send(content=content, files=channel_files)

                        for file_info in msg.get("files", []):
                            try:
                                os.remove(file_info["path"])
                            except Exception as e:
                                print(f"Error removing file {file_info['path']}: {e}")

                        schedule_manager.remove_message(msg)
                    
                    except Exception as e:
                        print(f"Error processing scheduled message: {e}")

                await asyncio.sleep(60)
        
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Schedule runner encountered an error: {e}")
            self._task = None
            await self.start()
