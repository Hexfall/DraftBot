import discord
from discord import Interaction, ButtonStyle
from discord.ui import View, Button

from Views.UserOptionChoiceView import UserOptionChoiceView


class DraftPickView(View):
    def __init__(self, user: discord.Member, options: list[str]):
        super().__init__(timeout=60*60*24*7)
        self.user = user
        self.option_select = UserOptionChoiceView(self, options + ["Mulligan"], row=1)
        self.option_select.callback = self.choice_changed
        self.submit_button = Button(label="Submit", style=ButtonStyle.green, disabled=True, row=4)
        self.submit_button.callback = self.__callback
        self.add_item(self.submit_button)

    async def choice_changed(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your pick. Wait your turn.", ephemeral=True)
            return
        await interaction.response.defer()
        self.submit_button.disabled = False
        self.option_select.option_select.placeholder = self.option_select.get_option()
        await interaction.edit_original_response(view=self)
    
    async def __callback(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your pick. Wait your turn.", ephemeral=True)
            return
        await self.callback(interaction, self.option_select.get_option())
    
    async def callback(self, interaction: Interaction, option: str):
        pass
        