import discord
from discord import Guild, Interaction
from discord.ui import View

from Models.ModelBase import InteractionChannel
from Models.OptionsModel import OptionsModel
from Views.UserOptionChoiceView import UserOptionChoiceView


class EditPotView(View):
    def __init__(self, guild: Guild, channel: InteractionChannel):
        super().__init__(timeout=60*60*24*7)
        self.guild = guild
        self.channel = channel

        self.pot_options = UserOptionChoiceView(self, [], row=0, option_placeholder="Options in pot (select to remove)")
        self.available_options = UserOptionChoiceView(self, [], row=2, option_placeholder="Available options (select to add to pot)")

        self.pot_options.page_display.style = discord.ButtonStyle.green
        self.available_options.page_display.style = discord.ButtonStyle.blurple

        self.pot_options.callback = self.__rem_callback
        self.available_options.callback = self.__add_callback

        self.update_options()

    def update_options(self):
        with OptionsModel(self.guild, self.channel) as options_model:
            self.pot_options.options = options_model.get_pot()
            self.available_options.options = options_model.get_available_add_options()
        self.pot_options.update_options()
        self.available_options.update_options()

    async def __add_callback(self, interaction: Interaction):
        option = self.available_options.get_option()
        with OptionsModel(self.guild, self.channel) as options_model:
            options_model.add_pot(option)
        self.update_options()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"{interaction.user.mention} added *{option}* to the pot.")

    async def __rem_callback(self, interaction: Interaction):
        option = self.pot_options.get_option()
        with OptionsModel(self.guild, self.channel) as options_model:
            options_model.remove_pot(option)
        self.update_options()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"{interaction.user.mention} removed *{option}* from the pot.")
