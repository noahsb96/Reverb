import json
import os
from typing import List, Dict, Any

SCHEDULED_FILE = "scheduled.json"

class ScheduleManager:
    def __init__(self):
        self._messages: List[Dict[str, Any]] = []
        self.load_messages()

    def load_messages(self):
        """Load scheduled messages from file"""
        if os.path.exists(SCHEDULED_FILE):
            try:
                with open(SCHEDULED_FILE, 'r') as f:
                    self._messages = json.load(f)
            except json.JSONDecodeError:
                print("Error loading scheduled messages file")
                self._messages = []
        else:
            self._messages = []

    def save_messages(self):
        """Save messages to file"""
        with open(SCHEDULED_FILE, 'w') as f:
            json.dump(self._messages, f, indent=2)

    def add_message(self, message: Dict[str, Any]):
        """Add a new scheduled message"""
        self._messages.append(message)
        self.save_messages()

    def remove_message(self, message: Dict[str, Any]):
        """Remove a scheduled message"""
        self._messages.remove(message)
        self.save_messages()

    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Get all scheduled messages"""
        return self._messages

schedule_manager = ScheduleManager()

def load_scheduled_messages():
    schedule_manager.load_messages()
    return schedule_manager.messages

def save_scheduled_messages(messages=None):
    if messages is not None:
        schedule_manager._messages = messages
    schedule_manager.save_messages()

def add_scheduled_message(message):
    schedule_manager.add_message(message)

def remove_scheduled_message(message):
    schedule_manager.remove_message(message)
