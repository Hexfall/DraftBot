import discord
from discord import Guild, Interaction, User
from discord.ui import View, Button

from Models.ModelBase import InteractionChannel
from Models.OptionsModel import OptionsModel
from Views.UserOptionChoiceView import UserOptionChoiceView


class AutoAddView(View):
    def __init__(self, guild: Guild, channel: InteractionChannel, user: User):
        super().__init__(timeout=60 * 60 * 24 * 7)
        self.guild = guild
        self.channel = channel
        self.user = user

        self.options = UserOptionChoiceView(self, [], row=0,
                                            option_placeholder="Available options (select to add to pot)")
        self.auto_picks = UserOptionChoiceView(self, [], row=2,
                                               option_placeholder="Auto pot queue (select to remove)")

        self.auto_picks.page_display.style = discord.ButtonStyle.red
        self.options.page_display.style = discord.ButtonStyle.green

        self.auto_picks.callback = self.__rem_callback
        self.options.callback = self.__add_callback

        self.update_options()

    def update_options(self):
        with OptionsModel(self.guild, self.channel) as options_model:
            options = options_model.get_options()
            auto = options_model.get_auto_actions(self.user).get('picks', [])
            for opt in auto:
                if opt in options:
                    options.remove(opt)
            self.auto_picks.options = auto
            self.options.options = options
        self.auto_picks.update_options()
        self.options.update_options()

    async def __add_callback(self, interaction: Interaction):
        option = self.options.get_option()
        with OptionsModel(self.guild, self.channel) as options_model:
            options_model.add_auto_pick(self.user, option)
        self.update_options()
        await interaction.response.edit_message(view=self)

    async def __rem_callback(self, interaction: Interaction):
        option = self.auto_picks.get_option()
        with OptionsModel(self.guild, self.channel) as options_model:
            options_model.remove_auto_pick(self.user, option)
        self.update_options()
        await interaction.response.edit_message(view=self)
