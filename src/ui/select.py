"""Channel selection components."""

from typing import Dict, List

import discord

class ChannelSelect(discord.ui.Select):
    """Select menu for choosing channels."""

    def __init__(
        self, 
        options: Dict[str, int], 
        attachment, 
        is_schedule: bool, 
        selected_values: List[str] = None
    ):
        self.attachment = attachment
        self.is_schedule = is_schedule
        self.all_options = options
        self._selected = selected_values or []
        
        filtered_options = []
        name_by_id = {str(cid): name for name, cid in options.items()}
        
        # Create select options
        for name, cid in options.items():
            str_cid = str(cid)
            is_selected = str_cid in self._selected
            
            option = discord.SelectOption(
                label=name[:25],
                value=str_cid,
                default=is_selected
            )
            filtered_options.append(option)
        
        # Create the placeholder text    
        if self._selected:
            selected_names = [name_by_id[val][:15] for val in self._selected if val in name_by_id]
            if len(selected_names) > 2:
                placeholder = f"Selected: {selected_names[0]} +{len(selected_names)-1} more"
            elif selected_names:
                placeholder = f"Selected: {', '.join(selected_names)}"
            else:
                placeholder = "Select channels to post in..."
        else:
            placeholder = "Select channels to post in..."
        
        super().__init__(
            placeholder=placeholder,
            min_values=0,
            max_values=len(filtered_options),
            options=filtered_options
        )

    def _update_select_state(self):
        """Update the selection state of all options."""
        for option in self.options:
            option.default = option.value in self._selected

    def _update_placeholder(self):
        """Update the placeholder text based on current selection."""
        name_by_id = {str(cid): name for name, cid in self.all_options.items()}
        selected_names = [name_by_id[val][:15] for val in self._selected if val in name_by_id]
        if len(selected_names) > 2:
            self.placeholder = f"Selected: {selected_names[0]} +{len(selected_names)-1} more"
        elif selected_names:
            self.placeholder = f"Selected: {', '.join(selected_names)}"
        else:
            self.placeholder = "Select channels to post in..."

    def _update_confirm_button(self):
        """Update the confirm button state based on current selection."""
        confirm_button = next(
            (item for item in self.view.children if isinstance(item, discord.ui.Button) and item.custom_id == "confirm"),
            None
        )
        
        if confirm_button:
            if self._selected:
                confirm_button.disabled = False
                if len(self._selected) > 1:
                    confirm_button.label = f"Confirm ({len(self._selected)} selected)"
                elif len(self._selected) == 1:
                    full_name_by_id = {str(cid): name for name, cid in self.view.all_options.items()}
                    channel_name = full_name_by_id.get(self._selected[0], "Unknown")[:15]
                    confirm_button.label = f"Confirm: {channel_name}"
                else:
                    confirm_button.disabled = True
                    confirm_button.label = "Confirm Selection"
            else:
                confirm_button.disabled = True
                confirm_button.label = "Confirm Selection"

    async def callback(self, interaction: discord.Interaction):
        """Handle selection changes."""
        visible_options = {opt.value for opt in self.options}
        preserved_selections = [val for val in self.view.selected_values if val not in visible_options]
        current_selections = list(self.values)
        self._selected = preserved_selections + current_selections
        self.view.selected_values = self._selected
        self._update_select_state()
        self._update_placeholder()
        self._update_confirm_button()
        
        await interaction.response.edit_message(view=self.view)
