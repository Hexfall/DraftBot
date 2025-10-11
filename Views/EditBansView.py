import discord
from discord import Guild, Interaction
from discord.ui import View

from Models.ModelBase import InteractionChannel
from Models.OptionsModel import OptionsModel
from Views.UserOptionChoiceView import UserOptionChoiceView


class EditBansView(View):
    def __init__(self, guild: Guild, channel: InteractionChannel):
        super().__init__(timeout=60*60*24*7)
        self.guild = guild
        self.channel = channel

        self.banned_options = UserOptionChoiceView(self, [], row=0, option_placeholder="Banned options (select to unban)")
        self.unbanned_options = UserOptionChoiceView(self, [], row=2, option_placeholder="Unbanned options (select to ban)")
        
        self.banned_options.page_display.style = discord.ButtonStyle.red
        self.unbanned_options.page_display.style = discord.ButtonStyle.green
        
        self.banned_options.callback = self.__rem_callback
        self.unbanned_options.callback = self.__add_callback
        
        self.update_options()
        
    def update_options(self):
        with OptionsModel(self.guild, self.channel) as options_model:
            self.banned_options.options = options_model.get_bans()
            self.unbanned_options.options = options_model.get_unbanned_options()
        self.banned_options.update_options()
        self.unbanned_options.update_options()

    async def __add_callback(self, interaction: Interaction):
        option = self.unbanned_options.get_option()
        with OptionsModel(self.guild, self.channel) as options_model:
            options_model.add_ban(option)
        self.update_options()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"{interaction.user.mention} banned {option}.")
    
    async def __rem_callback(self, interaction: Interaction):
        option = self.banned_options.get_option()
        with OptionsModel(self.guild, self.channel) as options_model:
            options_model.remove_ban(option)
        self.update_options()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"{interaction.user.mention} unbanned {option}.")
