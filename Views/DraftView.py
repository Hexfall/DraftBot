import discord
from discord import ButtonStyle, SelectOption, Interaction
from discord.ui import View, UserSelect, Button, Select

from Models.ModelBase import InteractionChannel
from Views.BoolButton import BoolButton

DEFAULT_SELECT = 3

class DraftView(View):
    def __init__(self, guild: discord.Guild, channel: InteractionChannel):
        super().__init__(timeout=60*60*24*7)
        self.guild = guild
        self.channel = channel
        
        self.users = UserSelect(
            placeholder="Select users",
            min_values=1,
            max_values=25,
            row=0,
        )

        self.bans = Select(
            placeholder=f"Bans per player (default {DEFAULT_SELECT})",
            options=[SelectOption(label=str(i)) for i in range(0, 11)],
            row=1,
        )

        self.picks = Select(
            placeholder=f"Picks per player (default {DEFAULT_SELECT})",
            options=[SelectOption(label=str(i)) for i in range(0, 11)],
            row=2,
        )

        self.options = Select(
            placeholder=f"Options per player (default {DEFAULT_SELECT})",
            options=[SelectOption(label=str(i)) for i in range(0, 11)],
            row=3,
        )
        
        self.start_button = Button(
            label="Start draft",
            style=ButtonStyle.primary
        )
        
        self.clear_bans_button = BoolButton(
            label="Clear bans",
            starting_value=True
        )
        
        self.clear_pot_button = BoolButton(
            label="Clear pot",
            starting_value=True
        )
        
        self.forgo_pot_button = BoolButton(
            label="Use all options",
            starting_value=False
        )

        self.users.callback = self.user_select_callback
        self.bans.callback = ignore
        self.picks.callback = ignore
        self.options.callback = ignore
        self.start_button.callback = self.start_draft 
        self.clear_bans_button.callback = self.clear_bans_callback
        self.clear_pot_button.callback = self.clear_pot_callback
        self.forgo_pot_button.callback = self.forgo_pot_callback

        self.add_item(self.users)
        self.add_item(self.bans)
        self.add_item(self.picks)
        self.add_item(self.options)
        self.add_item(self.clear_bans_button)
        self.add_item(self.clear_pot_button)
        self.add_item(self.forgo_pot_button)
        self.add_item(self.start_button)
    
    async def callback(self, interaction: Interaction, users: list[discord.User], bans: int, picks: int, options: int, clear_bans: bool = False, clear_picks: bool = False, forgo_picks: bool = False):
        pass
    
    async def user_select_callback(self, interaction: Interaction):
        if self.__valid_users():
            await interaction.response.defer()
            return
        await interaction.response.send_message("Draft must include at least one user and no bots", ephemeral=True)

    async def clear_bans_callback(self, interaction: Interaction):
        self.clear_bans_button.toggle()
        await interaction.response.edit_message(view=self)

    async def clear_pot_callback(self, interaction: Interaction):
        self.clear_pot_button.toggle()
        await interaction.response.edit_message(view=self)

    async def forgo_pot_callback(self, interaction: Interaction):
        self.forgo_pot_button.toggle()
        if self.forgo_pot_button.value:
            self.remove_item(self.picks)
            self.remove_item(self.clear_pot_button)
            self.forgo_pot_button.label = "(No pot)"
        else:
            self.add_item(self.picks)
            self.remove_item(self.forgo_pot_button)
            self.remove_item(self.start_button)
            self.add_item(self.clear_pot_button)
            self.add_item(self.forgo_pot_button)
            self.add_item(self.start_button)
            self.forgo_pot_button.label = "Use all options"
        await interaction.response.edit_message(view=self)
    
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
        if not self.forgo_pot_button.value:
            s += f"**Picks per player:** {self.get_picks_per_player()}\n"
        s += f"**Options per player:** {self.get_options_per_player()}\n"
        s += f"**Forgo picks and use all options:** {'yes' if self.forgo_pot_button.value else 'no'}\n"
        s += f"**Clear bans:** {'yes' if self.clear_bans_button.value else 'no'}\n"
        if not self.forgo_pot_button.value:
            s += f"**Clear pot:** {'yes' if self.clear_pot_button.value else 'no'}\n"
        
        
        s += "\n- ".join(["## Players"] + list(map(lambda x: x.mention, self.get_users())))
        
        return s

    async def start_draft(self, interaction: Interaction):
        if not self.__valid_users():
            await interaction.response.send_message("Invalid users for draft", ephemeral=True)
            return
        await interaction.channel.send(self.__get_draft_message(interaction))
        await self.callback(
            interaction,
            self.get_users(),
            self.get_bans_per_player(),
            self.get_picks_per_player(),
            self.get_options_per_player(),
            self.clear_bans_button.value,
            self.clear_pot_button.value,
            self.forgo_pot_button.value,
        )
    
async def ignore(interaction: Interaction):
    await interaction.response.defer()
