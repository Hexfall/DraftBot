import asyncio
import time
from asyncio import TaskGroup
from random import shuffle, seed, random
from threading import Lock

import discord

from Models.PlayerModel import PlayerModel
from Models.PotModel import PotModel
from Models.RulesModel import RulesModel

PREFIX = "!draft"

class DraftBot(discord.Client):
    def __init__(self, intents: discord.Intents = discord.Intents.default()):
        super().__init__(intents=intents)
    
    async def on_ready(self):
        print('Logged in as: {0} {1}'.format(self.user.name, self.user.id))
    
    async def on_message(self, message: discord.message.Message):
        if message.author == self.user:
            return

        if message.guild is None:
            # This is a DM. Deal with later.
            print("Got DM")
            return
        
        if message.content.startswith(PREFIX):
            await self.parse_message(message, message.content[len(PREFIX):].strip())
    
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user == self.user:
            return
        if reaction.message.guild is None:
            return
        
        async for u in reaction.users():
            if u == self.user:
                if random() < 0.1:
                    await reaction.message.channel.send(f"You think you're fucking funny {user.mention}? You think you can do my job better than me? Is that it maybe? \nNo?\nI didn't fucking think so. I run this fucking place and you're just some upstart turd. If you know what's fucking good for you, you'll leave me to my business and pray that I never notice you again. Know your fucking place.\nBitch ass punk.")
                    break

    async def parse_message(self, message: discord.message.Message, command):
        try:
            com, mantissa = command.split(" ")[0], " ".join(command.split(" ")[1:])
            await getattr(self, com.lower().strip())(message, mantissa)
        except AttributeError as err:
            await message.channel.send("Invalid syntax. !draft help for help.")
            print(f"Failed to parse message. {err}")
        except Exception as err:
            print(f"Failed to an unknown command. {err}")
    
    async def help(self, message: discord.message.Message, command):
        s = '''
```
!draft
    ⊢ players
        ⊢ show                          # Shows the current players on this server.
        ⊢ add <player> [player]...      # Adds a player to the draft.
        ⊢ remove <player> [player]...   # Removes a player from the draft.
        ⊢ clear                         # Removes all players from the draft.
    ⊢ pot
        ⊢ draft                         # Begin a snakedraft with the current players.
        ⊢ show                          # Shows the current options in the pot.
        ⊢ add <option>                  # Adds a new option to the draft.
        ⊢ remove <option>               # Removes an option from the draft.
        ⊢ clear                         # Removes all options from the draft.
    ⊢ rules
        ⊢ allowmulligans <y|n>          # Changes whether or not to allow mulligans during draft.
        ⊢ optionsperplayer <number>     # Changes the amount of options given to each players (and rounds in pot draft).
        ⊢ publicdraft <y|n>             # Whether players' options are public, or only given in DMs.
    ⊢ remind <@user> <duration[(h)|m]> <message>
    ⊢ draft                             # Draft options to players.
```'''
        await message.channel.send(s)
    
    async def echo(self, message: discord.message.Message, text):
        await message.channel.send(f"{text}")
        
    async def ping(self, message: discord.message.Message, text):
        await message.channel.send(message.author.mention)
        await message.channel.send(message.guild.name)
        
    async def remind(self, message: discord.message.Message, text):
        try:
            user, duration, remind_message = text.split(" ", 2)
        except:
            await message.channel.send("Invalid syntax. Correct form is `!draft remind <@user> <duration[(h)|m]> <reminder message>`")
            return

        if duration.isdigit():
            duration = int(duration) * 60 * 60
        else:
            fails = True
            
            if not duration[:-1].isdigit():
                pass
            elif duration[-1] == "h":
                duration = int(duration[:-1]) * 60 * 60
                fails = False
            elif duration[-1] == "m":
                duration = int(duration[:-1]) * 60
                fails = False
            
            if fails:
                await message.channel.send("Failed to parse duration. Please try again.")
                return
        
        async for u in message.guild.fetch_members(limit=None):
            if u.mention == user or u.display_name == user or u.name == user:
                user = u
                break
        else:
            await message.channel.send(f"Failed to find user {user}. Please try again.")
            return

        await message.add_reaction("👍")
        await asyncio.sleep(duration)
        await message.channel.send(f"{user.mention} {remind_message}")
        
    async def players(self, message: discord.message.Message, text):
        com, mantissa = text.split(" ")[0].lower().strip(), " ".join(text.split(" ")[1:])
        m = PlayerModel(str(message.channel.id))
        if com == "show":
            await message.channel.send('\n- '.join([f"There are currently {len(m.data)} players in the draft:"] + m.data))
        elif com == "add":
            for p in mantissa.split():
                for u in message.guild.members:
                    if u.mention == p.strip():
                        if u.bot:
                            await message.reply(f"Bots cannot play games.")
                        else:
                            break # User is on server and is not a bot. All good.
                else:
                    await message.reply(f"{p} is not a user on this server.")
                    continue
                m.add_player(p.strip())
            await message.add_reaction("👍")
        elif com == "remove":
            for p in mantissa.split():
                m.rem_player(p.strip())
            await message.add_reaction("👍")
        elif com == "clear":
            m.clear_players()
            await message.add_reaction("👍")
        elif com == "random":
            seed(time.time())
            p = m.data.copy()
            shuffle(p)
            await message.channel.send("\n".join(["Here's your randomly ordered list of players:"] + [f"{i+1}. {u}" for i, u in enumerate(p)]))
        else:
            await message.channel.send("Invalid syntax. !draft help for help.")
            await message.author.send("This is a dm")
    
    async def pot(self, message: discord.message.Message, text):
        com, mantissa = text.split(" ")[0].lower().strip(), " ".join(text.split(" ")[1:])
        if com == "show":
            m = PotModel(str(message.channel.id))
            await message.channel.send('\n- '.join([f"There are currently {len(m.data)} options in the pot:"] + m.data))
        elif com == "add":
            m = PotModel(str(message.channel.id))
            m.add_pot(mantissa.strip())
            await message.add_reaction("👍")
        elif com == "remove":
            m = PotModel(str(message.channel.id))
            m.rem_pot(mantissa.strip())
            await message.add_reaction("👍")
        elif com == "clear":
            m = PotModel(str(message.channel.id))
            m.clear_pot()
            await message.add_reaction("👍")
        elif com == "draft":
            await self.draft_pot(message)
        else:
            await message.channel.send("Invalid syntax. !draft help for help.")

    async def rules(self, message: discord.message.Message, text):
        com, mantissa = text.split(" ")[0].lower().strip(), " ".join(text.split(" ")[1:])
        m = RulesModel(str(message.channel.id))
        if com == "allowmulligans":
            if mantissa.strip().lower() == "y":
                m.set_mulligans(True)
            elif mantissa.strip().lower() == "n":
                m.set_mulligans(False)
            else:
                return await message.channel.send("Invalid syntax. !draft help for help.")
            await message.add_reaction("👍")
        elif com == "optionsperplayer":
            try:
                m.set_options(int(mantissa.strip()))
            except ValueError:
                return await message.channel.send("Invalid syntax. !draft help for help.")
            await message.add_reaction("👍")
        elif com == "publicdraft":
            if mantissa.strip().lower() == "y":
                m.set_public(True)
            elif mantissa.strip().lower() == "n":
                m.set_public(False)
            await message.add_reaction("👍")
        else:
            await message.channel.send("Invalid syntax. !draft help for help.")
    
    async def draft(self, message: discord.message.Message, text):
        print(f"Initiating draft in {message.channel.name} on {message.guild.name}.")
        rm = RulesModel(str(message.channel.id))
        pm = PlayerModel(str(message.channel.id))
        om = PotModel(str(message.channel.id))
        
        if len(pm.data) * rm.data["options"] > len(om.data):
            return await message.channel.send(f"Not enough options in pot to draft {rm.data['options']} options to each player. You need {len(pm.data) * rm.data["options"]} options to draft for {len(pm.data)} players, but you only have {len(om.data)} options currently.")
        
        pick_lock = Lock()
        picks = dict(zip(pm.data, ["Mulligan"] * len(pm.data)))
        round = 0
        
        while any([p == "Mulligan" for p in picks.values()]):
            async def get_pick(user: str, options: list[str]) -> None:
                try:
                    print("entered func")
                    os = options.copy()
                    if rm.data["mulligans"]:
                        os.append("Mulligan")
                    
                    for u in message.guild.members:
                        if u.mention == user:
                            print("found user")
                            s = "\n- ".join(["Your options are:"] + [f"{i+1}. {o}" for i, o in enumerate(os)])
                            s += "\nRespond with a message here or in the channel being used for the draft with the number of the option you'd like to pick."
                            await u.send(s)
                            
                            def is_pick(m) -> bool:
                                return m.author == u and (m.channel == message.channel or m.guild is None) and m.content.isdigit() and 0 < int(m.content) <= len(os)
                            
                            try:
                                pick = await self.wait_for('message', check=is_pick, timeout=60.0*60.0*24*4) # Four-day timeout
                            except asyncio.TimeoutError:
                                return await message.channel.send(f"{u} failed to pick before the timeout.")

                            pick_lock.acquire()
                            picks[user] = os[int(pick.content) - 1]
                            pick_lock.release()
                            await pick.add_reaction("👍")
                            print(f"Got pick from {u.display_name}")

                            break
                    else:
                        print("failed to find user")
                except Exception as err:
                    print(f"Error in sub-group. {err}")
            
            optlist = om.data.copy()
            for p in picks.values():
                if p in optlist:
                    optlist.remove(p)
            seed(time.time())
            shuffle(optlist)
            options = dict(zip(pm.data, [[optlist.pop() for _ in range(rm.data["options"] - round)] for _ in range(len(pm.data))]))
            
            if (rm.data["options"] - round) == 1:
                for k, v in picks.items():
                    if v == "Mulligan":
                        picks[k] = options[k][0]
                break
            
            if rm.data["public"]:
                await message.channel.send("\n- ".join(["Draft step ready: "] + [(f"{k}: {picks[k]}" if picks[k] != "Mulligan" else f"{k}:\n  - {'\n  - '.join(v)}") for k, v in options.items()]))
            
            async with TaskGroup() as tg:
                print("entered task group")
                for k, v in picks.items():
                    if v != "Mulligan":
                        continue
                    print("Creating task for user")
                    try:
                        tg.create_task(
                            get_pick(k, options[k])
                        )
                    except Exception as err:
                        print(f"Error in sub-group. {err}")
            
            round += 1
        
        await message.channel.send("\n- ".join(["Draft has been finalized:"] + [f"{k}: {v}" for k, v in picks.items()]))
        
    async def draft_pot(self, message: discord.message.Message):
        seed(time.time())
        with PlayerModel(str(message.channel.id)) as pm:
            p = pm.data.copy()
        with PotModel(str(message.channel.id)) as om:
            om.clear_pot()
        shuffle(p)
        await message.channel.send("\n".join(["Picks will be added to the pot using snake draft with the following randomly ordered list of players:"] + [f"{i+1}. {u}" for i, u in enumerate(p)]))
        order = p.copy()
        with RulesModel(str(message.channel.id)) as rm:
            for i in range(rm.data["options"] - 1):
                if i % 2 == 0:
                    order += p[::-1]
                else:
                    order += p
        
        while not len(order) == 0:
            player = order.pop(0)
            await message.channel.send(f"It is your turn to pick {player}. Start your message with '?' to add your pick to the pot.")

            def is_pick(m) -> bool:
                return m.author.mention == player and m.channel == message.channel and m.content.startswith("?") and len(m.content) > 1

            try:
                pick: discord.message.Message = await self.wait_for('message', check=is_pick, timeout=60.0*60.0*24*4) # Four-day timeout
            except asyncio.TimeoutError:
                return await message.channel.send(f"{player} failed to pick before the timeout. Terminating draft.")
            
            with PotModel(str(message.channel.id)) as om:
                om.add_pot(pick.content[1:])
            await pick.add_reaction("👍")

        with PotModel(str(message.channel.id)) as om:
            await message.channel.send('\n- '.join([f"Here are the finalized options in the pot:"] + om.data))
            
