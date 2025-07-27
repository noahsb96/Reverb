import discord

def create_help_embed():
    help_embed = discord.Embed(
        title="Reverb Bot Commands",
        description="Here's a list of all available commands and how to use them:",
        color=discord.Color.blue()
    )
    
    help_embed.add_field(
        name="/postmessage",
        value=(
            "Post a message to multiple channels at once.\n"
            "• Optional: Attach a file when using the command\n"
            "• Select which channels to post to\n"
            "• Add your message text (optional)\n"
            "The message will show who sent it."
        ),
        inline=False
    )
    
    help_embed.add_field(
        name="/schedulemessage",
        value=(
            "Schedule a message to be posted later.\n"
            "• Optional: Attach a file when using the command\n"
            "• Select which channels to post to\n"
            "• Add your message text (optional)\n"
            "• Set the date and time (format: MM/DD/YYYY HH:MM AM/PM)\n"
            "The message will show who scheduled it when it's posted."
        ),
        inline=False
    )
    
    help_embed.add_field(
        name="/help",
        value="Show this help message with all available commands.",
        inline=False
    )

    help_embed.set_footer(text="All interactions with the bot are private - other users won't see you using the commands.")
    
    return help_embed
