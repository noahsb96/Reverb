"""Channel view components."""

from typing import Dict, TYPE_CHECKING

import discord
from discord.ui import View

from .modals import MessageModal, ScheduleModal

if TYPE_CHECKING:
    from .select import ChannelSelect


class ChannelSearchModal(discord.ui.Modal):
    """Modal for searching channels."""
    
    def __init__(self, channel_view: 'ChannelView'):
        super().__init__(title="Search Channels")
        self.channel_view = channel_view
        self.search_input = discord.ui.TextInput(
            label="Search channels",
            placeholder="Type to filter channels...",
            required=True,
            max_length=100
        )
        self.add_item(self.search_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Process the search input and update the channel list."""
        search_term = self.search_input.value.lower()
        self.channel_view.update_channel_list(search_term)
        await interaction.response.edit_message(view=self.channel_view)

from .select import ChannelSelect  # Has to be imported after ChannelSearchModal

class ChannelView(View):
    """View for selecting and managing channels."""

    def __init__(self, options: Dict[str, int], attachment, is_schedule: bool = False):
        super().__init__(timeout=180)
        self.all_options = options
        self.attachment = attachment
        self.is_schedule = is_schedule
        self.selected_values = []
        
        # Add buttons
        self.add_item(discord.ui.Button(
            label="🔍 Search Channels",
            style=discord.ButtonStyle.secondary,
            custom_id="search",
            row=0
        ))
        self.add_item(discord.ui.Button(
            label="Clear Search",
            style=discord.ButtonStyle.secondary,
            custom_id="clear",
            row=0
        ))
        self.add_item(discord.ui.Button(
            label="Confirm Selection",
            style=discord.ButtonStyle.primary,
            custom_id="confirm",
            row=2,
            disabled=True
        ))
        
        self.update_channel_list()

    def update_channel_list(self, search_term: str = ""):
        """Update the channel list based on search term."""
        # Remove existing select menu
        for item in self.children[:]:
            if isinstance(item, ChannelSelect):
                self.remove_item(item)

        # Filter channels based on search term
        filtered_options = {
            name: cid
            for name, cid in self.all_options.items()
            if search_term.lower() in name.lower()
        }

        # Add new select menu if there are matching channels
        if filtered_options:
            select_menu = ChannelSelect(
                filtered_options, 
                self.attachment, 
                self.is_schedule,
                selected_values=self.selected_values
            )
            select_menu.row = 1
            self.add_item(select_menu)

        # Update confirm button state
        confirm_button = next(
            (item for item in self.children if isinstance(item, discord.ui.Button) and item.custom_id == "confirm"),
            None
        )
        
        if confirm_button:
            if self.selected_values:
                confirm_button.disabled = False
                confirm_button.label = f"Confirm ({len(self.selected_values)} selected)"
            else:
                confirm_button.disabled = True
                confirm_button.label = "Confirm Selection"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Handle button interactions."""
        if interaction.data["custom_id"] == "search":
            select_menu = next((item for item in self.children if isinstance(item, ChannelSelect)), None)
            if select_menu and select_menu.values:
                self.selected_values = select_menu.values
            await interaction.response.send_modal(ChannelSearchModal(self))
            
        elif interaction.data["custom_id"] == "clear":
            self.update_channel_list("")
            await interaction.response.edit_message(view=self)
            
        elif interaction.data["custom_id"] == "confirm":
            if self.selected_values:
                selected_channels = [int(v) for v in self.selected_values]
                modal = ScheduleModal(selected_channels, self.attachment) if self.is_schedule else MessageModal(selected_channels, self.attachment)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message("Please select at least one channel first.", ephemeral=True)
        
        return True


