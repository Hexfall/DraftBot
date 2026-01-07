from asyncio import Lock
from datetime import datetime
from random import shuffle, seed, randint
from typing import Any

import discord
from discord import app_commands, Interaction, Member

from Models.CityStateModel import CityStateModel
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
    if private:
        await interaction.followup.send("\n- ".join([header_message] + items), ephemeral=True)
    else:
        await interaction.channel.send("\n- ".join([header_message] + items))


async def _send_bans(interaction: Interaction, private: bool):
    with OptionsModel(interaction.guild, interaction.channel) as options_model:
        bans = options_model.get_bans()
    await _send_list(interaction, private, f"There are currently {len(bans)} banned options:", bans)


async def _send_pot(interaction: Interaction, private: bool):
    with OptionsModel(interaction.guild, interaction.channel) as options_model:
        pot = options_model.get_pot()
    await _send_list(interaction, private, f"There are currently {len(pot)} options in the pot:", pot)
        

@app_commands.command(name="show_pot", description="Sends a message with a list of options currently in the pot. Visible only to you by default.")
async def get_pot(interaction: Interaction, private: bool = True):
    await _send_pot(interaction, private)


@app_commands.command(name="show_bans", description="Sends a message with a list of banned options. Visible only to you by default.")
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


@app_commands.command(description="Clears the list of banned options.")
async def clear_bans(interaction: Interaction):
    with OptionsModel(interaction.guild, interaction.channel) as options_model:
        options_model.clear_bans()
    await interaction.response.send_message(f"{interaction.user.mention} has cleared the bans list.")


@app_commands.command(description="Clears the list of options in the pot.")
async def clear_pot(interaction: Interaction):
    with OptionsModel(interaction.guild, interaction.channel) as options_model:
        options_model.clear_pot()
    await interaction.response.send_message(f"{interaction.user.mention} has cleared the pot.")


@app_commands.command(description="Gives a view for starting a draft, allowing for changing draft settings beforehand.")
async def draft(interaction: Interaction):
    async def callback(interaction: Interaction, users: list[discord.Member], bans: int, picks: int, options: int, clear_bans: bool = False, clear_picks: bool = False, forgo_picks: bool = False):
        await interaction.response.defer()
        with OptionsModel(interaction.guild, interaction.channel) as options_model:
            if clear_bans:
                options_model.clear_bans()
            if clear_picks:
                options_model.clear_pot()
        await ban_phase(interaction, users, bans)
        if not forgo_picks:
            await pick_phase(interaction, users, picks)
        await choose_phase(interaction, users, options, not forgo_picks)
    v = DraftView(interaction.guild, interaction.channel)
    v.callback = callback
    await interaction.response.send_message("Draft", view=v, ephemeral=True)


async def ban_phase(interaction: Interaction, users: list[discord.Member], bans: int):
    ban_queue, order = snake_order(users, bans)
    if bans != 0:
        await interaction.followup.send("Beginning banning phase. Banning will occur in a snake-draft format using the following order:\n- " + "\n- ".join([user.mention for user in order]))
    lock = Lock()
    for i, user in enumerate(ban_queue):
        async def callback(interaction: Interaction, option: str):
            await interaction.message.delete()
            await interaction.response.send_message(content=f"{interaction.user.mention} has banned *{option}*")
            lock.release()
        await lock.acquire()
        ban_view = AddBanView(interaction.guild, interaction.channel, user)
        ban_view.callback = callback
        ms_str = f"It is your turn to ban, {user.mention}.\n"
        if i == len(ban_queue) - 1:
            ms_str += "This is the final ban."
        else:
            isare = "is" if i == len(ban_queue) - 1 else "are"
            plural = "" if i == len(ban_queue) - 1 else "s"
            ms_str += f"There {isare} {len(ban_queue) - i} ban{plural} left.\n"
            remaining = ban_queue[i:].count(user)
            if remaining == 1:
                ms_str += "This is your last ban."
            else:
                ms_str += f"You have {remaining} remaining bans.\n"
        await interaction.channel.send(ms_str, view=ban_view)
    await lock.acquire()
    await _send_bans(interaction, False)


async def pick_phase(interaction: Interaction, users: list[discord.Member], picks: int):
    pot_queue, order = snake_order(users, picks)
    if picks != 0:
        await interaction.followup.send("Beginning picking phase. Picks will occur in a snake-draft format using the following order:\n- " + "\n- ".join([user.mention for user in order]))
    lock = Lock()
    for i, user in enumerate(pot_queue):
        async def callback(interaction: Interaction, option: str):
            await interaction.message.delete()
            await interaction.response.send_message(content=f"{interaction.user.mention} has added *{option}* to the pot")
            lock.release()
        await lock.acquire()
        pot_view = AddPotView(interaction.guild, interaction.channel, user)
        pot_view.callback = callback
        ms_str = f"It is your turn to pick, {user.mention}.\n"
        if i == len(pot_queue) - 1:
            ms_str += "This is the final pick."
        else:
            isare = "is" if i == len(pot_queue) - 1 else "are"
            plural = "" if i == len(pot_queue) - 1 else "s"
            ms_str += f"There {isare} {len(pot_queue) - i} pick{plural} left.\n"
            remaining = pot_queue[i:].count(user)
            if remaining == 1:
                ms_str += "This is your last pick."
            else:
                ms_str += f"You have {remaining} remaining picks.\n"
        await interaction.channel.send(ms_str, view=pot_view)
    await lock.acquire()
    await _send_pot(interaction, False)
    

async def choose_phase(interaction: Interaction, users: list[Member], options_per_player: int, use_pot: bool = True):
    user_picks: dict[discord.Member, str] = {}
    locks: dict[int, Lock] = {}
    for user in users:
        user_picks[user] = "Mulligan"
        locks[user.id] = Lock()
        await locks[user.id].acquire()
    message: discord.Message = None
        
    while any([p == "Mulligan" for p in user_picks.values()]):
        draft_message = "Draft step in progress. Players have been given the following options:\n"
        with OptionsModel(interaction.guild, interaction.channel) as options_model:
            if use_pot:
                options = options_model.get_shuffled_pot(*user_picks.values())
            else:
                options = options_model.get_shuffled_options(*user_picks.values())
        for user in users:
            user_options = sorted([options.pop() for _ in range(options_per_player)])
            if options_per_player == 1 and user_picks[user] == "Mulligan":
                user_picks[user] = user_options[0]
            if user_picks[user] != "Mulligan":
                draft_message += f"- {user.mention} :white_check_mark:: {user_picks[user]}\n"
                locks[user.id].release()
                continue
            
            async def callback(interaction: Interaction, option: str):
                await interaction.response.edit_message(content="Choice registered", view=None)
                nonlocal draft_message
                user_picks[interaction.user] = option
                draft_message = draft_message.replace(f"{interaction.user.mention} :x:", f"{interaction.user.mention} :white_check_mark:")
                await message.edit(content=draft_message)
                locks[interaction.user.id].release()
            pick_view = DraftPickView(user, user_options)
            pick_view.callback = callback
            await user.send("Select your pick", view=pick_view)
            draft_message += f"- {user.mention} :x::\n  - " + "\n  - ".join(user_options) + "\n"
        if options_per_player !=  1:
            message = await interaction.channel.send(draft_message)
            
        options_per_player -= 1
        for lock in locks.values():
            await lock.acquire()
    
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


@app_commands.command(name="random_number", description="Generates any amount of random numbers.")
async def random_number(interaction: Interaction, numbers: int = 1, min_value: int = 1, max_value: int = 8):
    seed(datetime.now().timestamp())
    nums = [str(randint(min_value, max_value)) for _ in range(numbers)]
    await interaction.response.send_message("\n- ".join([f"{interaction.user.mention} has generated {numbers} random numbers between {min_value} and {max_value}:"] + nums))


def city_state_message(city_states: dict[str, list[str]]) -> str:
    s = ""
    for k in sorted(city_states.keys()):
        s += f"**{k}** ({len(k)}):\n- " + "\n- ".join(city_states[k]) + "\n"
    return s


@app_commands.command(name="city_states", description="Generates any amount of unique city states for Civ 6.")
async def city_states(interaction: Interaction, amount: int = 12):
    with CityStateModel(interaction.guild) as city_state_model:
        city_states = city_state_model.get_city_states(amount)
    await interaction.response.send_message(f"{interaction.user} has generated {amount} random city states.\n{city_state_message(city_states)}")


@app_commands.command(name="city_states_by_type", description="Generates unique city states for Civ 6 with ability to specify how many of each type.")
async def city_states_by_type(interaction: Interaction, cultural: int = 2, industrial: int = 2, military: int = 2, religious: int = 2, scientific: int = 2, trade: int = 2):
    with CityStateModel(interaction.guild) as city_state_model:
        city_states = city_state_model.get_city_states_by_type(cultural, industrial, military, religious, scientific, trade)
    amount = sum([cultural, industrial, military, religious, scientific, trade])
    await interaction.response.send_message(f"{interaction.user} has generated {amount} random city states with type restrictions.\n{city_state_message(city_states)}")


@app_commands.command(name="city_states_balanced", description="Generates unique city states for Civ 6 with an equal amount ot each type.")
async def city_states_balanced(interaction: Interaction, amount_of_each_type: int = 2):
    with CityStateModel(interaction.guild) as city_state_model:
        types = len(city_state_model.data.keys())
        city_states = city_state_model.get_city_states_by_type(*([amount_of_each_type] * types))
    amount = amount_of_each_type * types
    await interaction.response.send_message(f"{interaction.user} has generated {amount} random city states with type restrictions.\n{city_state_message(city_states)}")


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
        self.tree.add_command(clear_pot)
        self.tree.add_command(clear_bans)
        self.tree.add_command(draft)
        self.tree.add_command(random_number)
        self.tree.add_command(city_states)
        self.tree.add_command(city_states_by_type)
        self.tree.add_command(city_states_balanced)
        # Sync the application command with Discord.
        await self.tree.sync()
        print("Completed command syncing.")
    
    async def on_ready(self):
        print('Logged in as: {0} {1}'.format(self.user.name, self.user.id))
        