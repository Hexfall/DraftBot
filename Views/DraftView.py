from asyncio import sleep

import discord
from discord import ButtonStyle, SelectOption, Interaction
from discord.ui import View, UserSelect, Button, Select

from Models.ModelBase import InteractionChannel


DEFAULT_SELECT = 3

class DraftView(View):
    def __init__(self, guild: discord.Guild, channel: InteractionChannel):
        super().__init__()
        self.guild = guild
        self.channel = channel
        
        self.users = UserSelect(
            placeholder="Select users",
            min_values=1,
            max_values=25,
        )

        self.bans = Select(
            placeholder=f"Bans per player (default {DEFAULT_SELECT})",
            options=[SelectOption(label=str(i)) for i in range(0, 11)]
        )

        self.picks = Select(
            placeholder=f"Picks per player (default {DEFAULT_SELECT})",
            options=[SelectOption(label=str(i)) for i in range(0, 11)]
        )

        self.options = Select(
            placeholder=f"Options per player (default {DEFAULT_SELECT})",
            options=[SelectOption(label=str(i)) for i in range(0, 11)]
        )
        
        self.start_button = Button(
            label="Start draft",
            style=ButtonStyle.primary
        )

        self.users.callback = self.user_select_callback
        self.bans.callback = ignore
        self.picks.callback = ignore
        self.options.callback = ignore
        self.start_button.callback = self.start_draft 

        self.add_item(self.users)
        self.add_item(self.bans)
        self.add_item(self.picks)
        self.add_item(self.options)
        self.add_item(self.start_button)
    
    async def callback(self, interaction: Interaction, users: list[discord.User], bans: int, picks: int, options: int):
        pass
    
    async def user_select_callback(self, interaction: Interaction):
        if self.__valid_users():
            await interaction.response.defer()
            return
        await interaction.response.send_message("Draft must include at least one user and no bots", ephemeral=True)
    
    def __valid_users(self) -> bool:
        if len(self.users.values) == 0:
            return False
        for user in self.users.values:
            if user.bot:
                return False
        return True
    
    def get_users(self) -> list[discord.User]:
        return list(self.users.values)
    
    def get_bans_per_player(self) -> int:
        if len(self.bans.values) == 0:
            return DEFAULT_SELECT
        return int(self.bans.values[0])
    
    def get_picks_per_player(self) -> int:
        if len(self.picks.values) == 0:
            return DEFAULT_SELECT
        return int(self.picks.values[0])
        
    def get_options_per_player(self) -> int:
        if len(self.options.values) == 0:
            return DEFAULT_SELECT
        return int(self.options.values[0])
    
    def __get_draft_message(self, interaction: Interaction) -> str:
        s = ""
        
        s += f"# {interaction.user.mention} has started a draft in this channel\n"
        
        s += f"## Settings\n"
        s += f"**Bans per player:** {self.get_bans_per_player()}\n"
        s += f"**Picks per player:** {self.get_picks_per_player()}\n"
        s += f"**Options per player:** {self.get_options_per_player()}\n"
        
        s += "\n- ".join(["## Players"] + list(map(lambda x: x.mention, self.get_users())))
        
        return s

    async def start_draft(self, interaction: Interaction):
        if not self.__valid_users():
            await interaction.response.send_message("Invalid users for draft", ephemeral=True)
            return
        await interaction.channel.send(self.__get_draft_message(interaction))
        await self.callback(interaction, self.get_users(), self.get_bans_per_player(), self.get_picks_per_player(), self.get_options_per_player())
    
async def ignore(interaction: Interaction):
    await interaction.response.defer()
