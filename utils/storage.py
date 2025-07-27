import json
import os

SCHEDULED_FILE = "scheduled.json"

# Global list of scheduled messages
scheduled_messages = []

def load_scheduled_messages():
    """Load scheduled messages from file and update the global list"""
    global scheduled_messages
    if not os.path.exists(SCHEDULED_FILE):
        scheduled_messages = []
    else:
        with open(SCHEDULED_FILE, 'r') as f:
            scheduled_messages = json.load(f)
    return scheduled_messages
    
def save_scheduled_messages(messages=None):
    """Save scheduled messages to file. If no messages provided, saves the global list"""
    global scheduled_messages
    if messages is not None:
        scheduled_messages = messages
    with open(SCHEDULED_FILE, 'w') as f:
        json.dump(scheduled_messages, f, indent=2)

def add_scheduled_message(message):
    """Add a new scheduled message and save to file"""
    global scheduled_messages
    scheduled_messages.append(message)
    save_scheduled_messages()

def remove_scheduled_message(message):
    """Remove a scheduled message and save to file"""
    global scheduled_messages
    scheduled_messages.remove(message)
    save_scheduled_messages()
