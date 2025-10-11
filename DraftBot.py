from asyncio import Lock
from importlib.resources import contents
from random import shuffle
from typing import Any

import discord
from discord import app_commands, Interaction, Guild

from Models.ModelBase import InteractionChannel
from Models.OptionsModel import OptionsModel
from Views.AddBanView import AddBanView
from Views.AddPotView import AddPotView
from Views.DraftPickView import DraftPickView
from Views.DraftView import DraftView
from Views.OptionsView import OptionsView


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
        await interaction.response.defer()
        with OptionsModel(interaction.guild, interaction.channel) as options_model:
            options_model.clear_bans()
            options_model.clear_pot()
        await ban_phase(interaction, users, bans)
        await pick_phase(interaction, users, picks)
        await choose_phase(interaction, users, options)
    v = DraftView(interaction.guild, interaction.channel)
    v.callback = callback
    await interaction.response.send_message("Draft", view=v, ephemeral=True)


async def ban_phase(interaction: Interaction, users: list[discord.Member], bans: int):
    ban_queue, order = snake_order(users, bans)
    await interaction.followup.send("Beginning banning phase. Banning will occur in a snake-draft format using the following order:\n- " + "\n- ".join([user.mention for user in order]))
    lock = Lock()
    for user in ban_queue:
        async def callback(interaction: Interaction, option: str):
            await interaction.message.delete()
            await interaction.response.send_message(content=f"{interaction.user.mention} has banned {option}")
            lock.release()
        await lock.acquire()
        ban_view = AddBanView(interaction.guild, interaction.channel, user)
        ban_view.callback = callback
        await interaction.followup.send(f"It is your turn to ban, {user.mention}", view=ban_view)
    await lock.acquire()
    lock.release()


async def pick_phase(interaction: Interaction, users: list[discord.Member], picks: int):
    pot_queue, order = snake_order(users, picks)
    await interaction.followup.send("Beginning picking phase. Picks will occur in a snake-draft format using the following order:\n- " + "\n- ".join([user.mention for user in order]))
    lock = Lock()
    for user in pot_queue:
        async def callback(interaction: Interaction, option: str):
            await interaction.message.delete()
            await interaction.response.send_message(content=f"{interaction.user.mention} has added {option} to the pot")
            lock.release()
        await lock.acquire()
        pot_view = AddPotView(interaction.guild, interaction.channel, user)
        pot_view.callback = callback
        await interaction.followup.send(f"It is your turn to add an option to the pot, {user.mention}", view=pot_view)
    await lock.acquire()
    lock.release()
    

async def choose_phase(interaction: Interaction, users: list[discord.Member], options_per_player: int):
    user_picks: dict[discord.Member, str] = {}
    locks: dict[discord.Member, Lock] = {}
    for user in users:
        user_picks[user] = "Mulligan"
        locks[user] = Lock()
        await locks[user].acquire()
        
    while any([p == "Mulligan" for p in user_picks.values()]):
        draft_message = "Draft step in progress. Players have been given the following options:\n"
        with OptionsModel(interaction.guild, interaction.channel) as options_model:
            options = options_model.get_shuffled_pot(*user_picks.values())
        for user in users:
            user_options = [options.pop() for _ in range(options_per_player)]
            if options_per_player == 1:
                user_picks[user] = user_options[0]
            if user_picks[user] != "Mulligan":
                locks[interaction.user].release()
                draft_message += f"- {user.mention}: {user_picks[user]}\n"
                continue
                
            async def callback(interaction: Interaction, option: str):
                await interaction.response.edit_message(content="Choice registered", view=None)
                user_picks[interaction.user] = option
                locks[interaction.user].release()
            pick_view = DraftPickView(user, user_options)
            pick_view.callback = callback
            await user.send("Select your pick", view=pick_view)
            draft_message += f"- {user.mention}:\n  - " + "\n  - ".join(user_options) + "\n"
        if options_per_player !=  1:
            await interaction.followup.send(draft_message)
            
        options_per_player -= 1
        for lock in locks.values():
            await lock.acquire()
    
    await interaction.followup.send("Draft complete. Results:\n- " + "\n- ".join([f"{k.mention}: {v}" for k, v in user_picks.items()]))
    

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
        