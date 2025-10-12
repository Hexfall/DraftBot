from asyncio import Lock
from random import shuffle
from typing import Any

import discord
from discord import app_commands, Interaction

from Models.OptionsModel import OptionsModel
from Views.AddBanView import AddBanView
from Views.AddPotView import AddPotView
from Views.DraftPickView import DraftPickView
from Views.DraftView import DraftView
from Views.EditBansView import EditBansView
from Views.EditPotView import EditPotView
from Views.OptionsView import OptionsView


@app_commands.command(name="edit_default_server_options", description="Changes the default options that are used in new threads/channels")
async def set_server_options(interaction: Interaction) -> None:
    await interaction.response.send_message("Server default options", view=OptionsView(interaction.guild), ephemeral=True)


async def _send_list(interaction: Interaction, private: bool, header_message: str, items: list[str]):
    if not interaction.response.is_done():
        await interaction.response.defer()
    await interaction.followup.send("\n- ".join([header_message] + items), ephemeral=private)


async def _send_bans(interaction: Interaction, private: bool):
    with OptionsModel(interaction.guild, interaction.channel) as options_model:
        bans = options_model.get_bans()
    await _send_list(interaction, private, f"There are currently {len(bans)} banned options:", bans)


async def _send_pot(interaction: Interaction, private: bool):
    with OptionsModel(interaction.guild, interaction.channel) as options_model:
        pot = options_model.get_pot()
    await _send_list(interaction, private, f"There are currently {len(pot)} options in the pot:", pot)
        

@app_commands.command(name="show_pot", description="Sends a message with a list of options currently in the pot. Only visible to you, unless specified as public.")
async def get_pot(interaction: Interaction, private: bool = True):
    await _send_pot(interaction, private)


@app_commands.command(name="show_bans", description="Sends a message with a list of options currently banned. Only visible to you, unless specified as public.")
async def get_bans(interaction: Interaction, private: bool = True):
    await _send_bans(interaction, private)


@app_commands.command(name="edit_options", description="Changes the options that are used in this thread/channel")
async def edit_options(interaction: Interaction):
    await interaction.response.send_message("Draft options", view=OptionsView(interaction.guild, interaction.channel), ephemeral=True)
    
    
@app_commands.command(description="Gives a display for moving options to and from the pot.")
async def edit_pot(interaction: Interaction):
    await interaction.response.send_message("Edit pot", view=EditPotView(interaction.guild, interaction.channel), ephemeral=True)


@app_commands.command(description="Gives a display for adding and removing options from the banned list.")
async def edit_bans(interaction: Interaction):
    await interaction.response.send_message("Edit bans", view=EditBansView(interaction.guild, interaction.channel), ephemeral=True)


@app_commands.command(description="Gives a view for starting a draft, allowing for changing draft settings beforehand.")
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
            await interaction.response.send_message(content=f"{interaction.user.mention} has banned *{option}*")
            lock.release()
        await lock.acquire()
        ban_view = AddBanView(interaction.guild, interaction.channel, user)
        ban_view.callback = callback
        await interaction.followup.send(f"It is your turn to ban, {user.mention}", view=ban_view)
    await lock.acquire()
    await _send_bans(interaction, False)


async def pick_phase(interaction: Interaction, users: list[discord.Member], picks: int):
    pot_queue, order = snake_order(users, picks)
    await interaction.followup.send("Beginning picking phase. Picks will occur in a snake-draft format using the following order:\n- " + "\n- ".join([user.mention for user in order]))
    lock = Lock()
    for user in pot_queue:
        async def callback(interaction: Interaction, option: str):
            await interaction.message.delete()
            await interaction.response.send_message(content=f"{interaction.user.mention} has added *{option}* to the pot")
            lock.release()
        await lock.acquire()
        pot_view = AddPotView(interaction.guild, interaction.channel, user)
        pot_view.callback = callback
        await interaction.followup.send(f"It is your turn to add an option to the pot, {user.mention}", view=pot_view)
    await lock.acquire()
    await _send_pot(interaction, False)
    

async def choose_phase(interaction: Interaction, users: list[discord.Member], options_per_player: int):
    user_picks: dict[discord.Member, str] = {}
    locks: list[Lock] = []
    for user in users:
        user_picks[user] = "Mulligan"
        
    while any([p == "Mulligan" for p in user_picks.values()]):
        draft_message = "Draft step in progress. Players have been given the following options:\n"
        with OptionsModel(interaction.guild, interaction.channel) as options_model:
            options = options_model.get_shuffled_pot(*user_picks.values())
        for user in users:
            user_options = [options.pop() for _ in range(options_per_player)]
            if options_per_player == 1:
                user_picks[user] = user_options[0]
            if user_picks[user] != "Mulligan":
                draft_message += f"- {user.mention}: {user_picks[user]}\n"
                continue
            
            l = Lock()
            await l.acquire()
            locks.append(l)
            async def callback(interaction: Interaction, option: str):
                await interaction.response.edit_message(content="Choice registered", view=None)
                user_picks[interaction.user] = option
                l.release()
            pick_view = DraftPickView(user, user_options)
            pick_view.callback = callback
            await user.send("Select your pick", view=pick_view)
            draft_message += f"- {user.mention}:\n  - " + "\n  - ".join(user_options) + "\n"
        if options_per_player !=  1:
            await interaction.followup.send(draft_message)
            
        options_per_player -= 1
        while len(locks) > 0:
            await locks.pop().acquire()
    
    await _send_list(interaction, False, "Draft complete. Results:", [f"{k.mention}: {v}" for k, v in user_picks.items()])
    

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
        # Sync the application command with Discord.
        await self.tree.sync()
        print("Completed command syncing.")
    
    async def on_ready(self):
        print('Logged in as: {0} {1}'.format(self.user.name, self.user.id))
        