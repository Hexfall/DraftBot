from math import ceil

from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import View, Select, Button

MAX_OPTIONS = 25


class UserOptionChoiceView:
    def __init__(self, parent_view: View, options: list[str], option_placeholder: str = "Choose option...", row: int = 0):
        self.parent = parent_view
        self.options = options
        
        self.page: int = 0
        self.buttons_visible: bool = False
        
        self.option_select = Select(
            placeholder=option_placeholder,
            options=[],
            min_values=0,
            max_values=1,
            row=row,
        )
        self.option_select.callback = self.__callback
        self.parent.add_item(self.option_select)
        
        self.prev_button = Button(label="◀ Previous", style=ButtonStyle.secondary, row=row+1)
        self.page_display = Button(label="Page 1/1", style=ButtonStyle.secondary, disabled=True, row=row+1)
        self.next_button = Button(label="Next ▶", style=ButtonStyle.secondary, row=row+1)

        self.prev_button.callback = self.prev_callback
        self.next_button.callback = self.next_callback
        
        self.update_options()
    
    async def __callback(self, interaction: Interaction):
        await self.callback(interaction)
    
    async def callback(self, interaction: Interaction):
        pass

    async def change_page(self, amount: int, interaction: Interaction):
        max_page = ceil(len(self.options) / MAX_OPTIONS)
        self.page = (self.page + amount) % max_page
        self.update_options()
        await interaction.response.edit_message(view=self.parent)

    async def next_callback(self, interaction: Interaction):
        await self.change_page(1, interaction)

    async def prev_callback(self, interaction: Interaction):
        await self.change_page(-1, interaction)

    def toggle_buttons(self):
        if self.buttons_visible:
            self.parent.remove_item(self.prev_button)
            self.parent.remove_item(self.page_display)
            self.parent.remove_item(self.next_button)
        else:
            self.parent.add_item(self.prev_button)
            self.parent.add_item(self.page_display)
            self.parent.add_item(self.next_button)
        self.buttons_visible = not self.buttons_visible

    def update_options(self):
        if self.page * MAX_OPTIONS > len(self.options):
            self.page = len(self.options) // MAX_OPTIONS
        opts = self.options[self.page * MAX_OPTIONS: (self.page + 1) * MAX_OPTIONS]
        self.option_select.options = [SelectOption(label=opt) for opt in opts]
        if len(self.options) == 0:
            self.option_select.options = [SelectOption(label="No options")]
        if len(self.options) <= MAX_OPTIONS and self.buttons_visible:
            self.toggle_buttons()
        elif len(self.options) > MAX_OPTIONS and not self.buttons_visible:
            self.toggle_buttons()
        max_page = ceil(len(self.options) / MAX_OPTIONS)
        self.page_display.label = f"Page {self.page+1}/{max_page}"
    
    def get_option(self) -> str:
        return self.option_select.values[0]
