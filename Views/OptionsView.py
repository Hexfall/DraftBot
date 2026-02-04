from datetime import timedelta
from math import ceil
from typing import Optional

from discord import Guild, SelectOption, Interaction, Message, ButtonStyle
from discord.ui import Select, View, Button, Modal, TextInput, UserSelect

from Models.GuildModel import GuildModel
from Models.ModelBase import InteractionChannel
from Models.OptionsModel import OptionsModel
from Views.UserOptionChoiceView import UserOptionChoiceView


class OptionsView(View):
    def __init__(self, guild: Guild, channel: Optional[InteractionChannel] = None):
        super().__init__(timeout=60*60*24*7)
        self.message: Optional[Message] = None
        
        self.preset: Select = None
        
        self.add_button = Button(label="Add option", style=ButtonStyle.primary, row=4)
        self.add_button.callback = self.add_callback
        
        self.guild: Guild = guild
        self.channel: Optional[InteractionChannel] = channel
        self.page = 0
        self.buttons_visible = False
        with (GuildModel(self.guild) if self.channel is None else OptionsModel(self.guild, self.channel)) as model:
            self._options = model.get_options()
            self.preset_names = model.get_preset_names()
            
        self.option = UserOptionChoiceView(self, self._options, "Options (select to remove)", row=1)
        self.option.callback = self.option_callback
        
        self.set_preset()
        self.add_item(self.add_button)
    
    def set_preset(self):
        self.preset = Select(
            placeholder="Options preset...",
            min_values=0,
            max_values=1,
            options=[],
        )
        self.preset.callback = self.preset_callback
        self.add_item(self.preset)
        self.update_preset()
    
    def update_preset(self):
        self.preset.options = [SelectOption(label=pn) for pn in self.preset_names]
        if len(self.preset_names) == 0:
            self.preset.options = [SelectOption(label="No presets")]
        
    async def preset_callback(self, interaction: Interaction):
        self.use_preset(self.preset.values[0])
        self.option.options = self._options
        self.option.update_options()
        await self.update_message(interaction)
        await interaction.response.edit_message(view=self)
    
    async def option_callback(self, interaction: Interaction):
        self.remove_option(self.option.option_select.values[0])
        self.update_options()
        await self.update_message(interaction)
        await interaction.response.edit_message(view=self)

    async def add_callback(self, interaction: Interaction):
        await interaction.response.send_modal(AddOptionModal(self))
    
    async def update_message(self, interaction: Interaction):
        if self.message == None or self.message.created_at < interaction.created_at - timedelta(minutes=10):
            self.message = await interaction.channel.send(f"{interaction.user.mention} has made changes to the {'default' if self.channel is None else 'draft'} options at <t:{int(interaction.created_at.timestamp())}>")
        else:
            await self.message.edit(content=f"{interaction.user.mention} has made changes to the {'default' if self.channel is None else 'draft'} options at <t:{int(interaction.created_at.timestamp())}>")
    
    def use_preset(self, preset_name: str):
        with (GuildModel(self.guild) if self.channel is None else OptionsModel(self.guild, self.channel)) as model:
            model.use_preset(preset_name)
            self._options = model.get_options()
    
    def add_option(self, option: str):
        with (GuildModel(self.guild) if self.channel is None else OptionsModel(self.guild, self.channel)) as model:
            model.add_option(option)
            self._options = model.get_options()
    
    def remove_option(self, option: str):
        with (GuildModel(self.guild) if self.channel is None else OptionsModel(self.guild, self.channel)) as model:
            model.remove_option(option)
            self._options = model.get_options()
            
    def update_options(self):
        self.option.options = self._options
        self.option.update_options()


class AddOptionModal(Modal, title="Add Option"):
    option_input = TextInput(
        label="Option Name",
        placeholder="Enter option to add...",
        required=True,
        max_length=100
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: Interaction):
        option_name = self.option_input.value.strip()
        if option_name:
            self.view.add_option(option_name)
            self.view.update_options()
            await self.view.update_message(interaction)
            await interaction.response.edit_message(view=self.view)