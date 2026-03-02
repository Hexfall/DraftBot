from importlib.resources import contents

import discord
from discord import Guild, Interaction, ButtonStyle
from discord.ui import View, Button

from Models.ModelBase import InteractionChannel
from Models.OptionsModel import OptionsModel
from Views.UserOptionChoiceView import UserOptionChoiceView


class AddBanView(View):
    def __init__(self, guild: Guild, channel: InteractionChannel, user: discord.User):
        super().__init__(timeout=60*60*24*7)
        self.user = user
        with OptionsModel(guild, channel) as options_model:
            options = options_model.get_unbanned_options()
        self.option_select = UserOptionChoiceView(self, options, row=1, owner=user)
        self.option_select.callback = self.choice_changed
        self.option_select.page_display.style = discord.ButtonStyle.red
        self.submit_button = Button(label="Submit", style=ButtonStyle.green, row=4)
        self.submit_button.callback = self.__callback
        self.add_item(self.submit_button)

    async def choice_changed(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your pick. Wait your turn.", ephemeral=True)
            return
        await interaction.response.defer()
    
    async def __callback(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your ban. Wait your turn.", ephemeral=True)
            return
        if not self.option_select.option_selected():
            await interaction.response.send_message("You don't have anything currently selected.", ephemeral=True)
            return
        with OptionsModel(interaction.guild, interaction.channel) as options_model:
            options_model.add_ban(self.option_select.get_option())
        await self.callback(interaction, self.option_select.get_option())
    
    async def callback(self, interaction: Interaction, option: str):
        pass
        