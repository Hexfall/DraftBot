from importlib.resources import contents

import discord
from discord import Guild, Interaction
from discord.ui import View

from Models.ModelBase import InteractionChannel
from Models.OptionsModel import OptionsModel
from Views.UserOptionChoiceView import UserOptionChoiceView


class AddPotView(View):
    def __init__(self, guild: Guild, channel: InteractionChannel, user: discord.User):
        super().__init__(timeout=60*60*24*7)
        self.user = user
        with OptionsModel(guild, channel) as options_model:
            options = options_model.get_available_add_options()
        self.option_select = UserOptionChoiceView(self, options, row=1)
        self.option_select.callback = self.__callback
        self.option_select.page_display.style = discord.ButtonStyle.green
    
    async def __callback(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your pick. Wait your turn.", ephemeral=True)
            return
        with OptionsModel(interaction.guild, interaction.channel) as options_model:
            options_model.add_pot(self.option_select.get_option())
        await self.callback(interaction, self.option_select.get_option())
    
    async def callback(self, interaction: Interaction, option: str):
        pass
        