from email.policy import default
from random import shuffle
from typing import Any

import discord
from discord import app_commands, Interaction, Guild

from Models.ModelBase import InteractionChannel
from Models.OptionsModel import OptionsModel
from Views.AddBanView import AddBanView
from Views.OptionsView import OptionsView
from Views.DraftView import DraftView


@app_commands.command(name="default_server_options", description="Changes the default options that are used in new threads/channels")
async def set_server_options(interaction: Interaction) -> None:
    await interaction.response.send_message("Server default options", view=OptionsView(interaction.guild), ephemeral=True)


@app_commands.command(name="show_pot")
async def get_pot(interaction: Interaction, private: bool = True):
    with OptionsModel(interaction.guild, interaction.channel) as options_model:
        pot = options_model.get_pot()
    await interaction.response.send_message("\n- ".join(["Current pot:"] + pot), ephemeral=private)


@app_commands.command(name="show_bans")
async def get_bans(interaction: Interaction, private: bool = True):
    with OptionsModel(interaction.guild, interaction.channel) as options_model:
        bans = options_model.get_bans()
    await interaction.response.send_message("\n- ".join(["Current bans:"] + bans), ephemeral=private)


@app_commands.command()
async def edit_options(interaction: Interaction):
    await interaction.response.send_message("Draft options", view=OptionsView(interaction.guild, interaction.channel), ephemeral=True)
    
    
@app_commands.command()
async def edit_pot(interaction: Interaction):
    pass


@app_commands.command()
async def edit_bans(interaction: Interaction):
    pass


@app_commands.command()
async def draft(interaction: Interaction):
    async def callback(interaction: Interaction, users: list[discord.Member], bans: int, picks: int, options: int):
        await interaction.response.send_message("\n".join([u.mention for u in snake_order(users, bans)[0]]))
    v = DraftView(interaction.guild, interaction.channel)
    v.callback = callback
    await interaction.response.send_message("Draft", view=v, ephemeral=True)
    

def snake_order(items: list[Any], times) -> tuple[list[Any], list[Any]]:
    l = items.copy()
    shuffle(l)
    ret = []
    for i in range(times):
        if i % 2 == 0:
            ret += l
        else:
            ret += l[::-1]
    return ret, l


async def start_draft(guild: Guild, channel: InteractionChannel, users: list[discord.Member], bans: int, picks: int, options: int):
    pass


async def ban_phase(guild: Guild, channel: InteractionChannel, users: list[discord.Member], bans: int):
    pass

@app_commands.command()
async def ban(interaction: Interaction):
    async def callback(interaction: Interaction, option: str):
        s = f"{interaction.user.mention} has banned {option}"
        await interaction.response.edit_message(content=s, view=None)
        await interaction.followup.send(s)
    v = AddBanView(interaction.guild, interaction.channel, interaction.user)
    v.callback = callback
    await interaction.response.send_message("Ban", view=v)


class DraftBot(discord.Client):
    def __init__(self, intents: discord.Intents = discord.Intents.default()):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.add_command(set_server_options)
        self.tree.add_command(get_pot)
        self.tree.add_command(get_bans)
        self.tree.add_command(edit_options)
        self.tree.add_command(edit_pot)
        self.tree.add_command(edit_bans)
        self.tree.add_command(draft)
        self.tree.add_command(ban)
        # Sync the application command with Discord.
        await self.tree.sync()
        print("Completed command syncing.")
    
    async def on_ready(self):
        print('Logged in as: {0} {1}'.format(self.user.name, self.user.id))
        