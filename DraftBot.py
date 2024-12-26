import time
from asyncio import TaskGroup
from random import shuffle, seed
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
        ⊢ show
        ⊢ add <player> [player]...
        ⊢ remove <player> [player]...
        ⊢ clear
    ⊢ pot
        ⊢ show
        ⊢ add <option>
        ⊢ remove <option>
        ⊢ clear
    ⊢ rules
        ⊢ allowmulligans <y|n>
        ⊢ optionsperplayer <number>
        ⊢ publicdraft <y|n>
    ⊢ draft
```'''
        await message.channel.send(s)
    
    async def echo(self, message: discord.message.Message, text):
        await message.channel.send(f"{text}")
        
    async def ping(self, message: discord.message.Message, text):
        await message.channel.send(message.author.mention)
        await message.channel.send(message.guild.name)
        
    async def players(self, message: discord.message.Message, text):
        com, mantissa = text.split(" ")[0].lower().strip(), " ".join(text.split(" ")[1:])
        m = PlayerModel(str(message.guild.id))
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
        else:
            await message.channel.send("Invalid syntax. !draft help for help.")
            await message.author.send("This is a dm")
    
    async def pot(self, message: discord.message.Message, text):
        com, mantissa = text.split(" ")[0].lower().strip(), " ".join(text.split(" ")[1:])
        m = PotModel(str(message.guild.id))
        if com == "show":
            await message.channel.send('\n- '.join([f"There are currently {len(m.data)} options in the pot:"] + m.data))
        elif com == "add":
            m.add_pot(mantissa.strip())
            await message.add_reaction("👍")
        elif com == "remove":
            m.rem_pot(mantissa.strip())
            await message.add_reaction("👍")
        elif com == "clear":
            m.clear_pot()
            await message.add_reaction("👍")
        else:
            await message.channel.send("Invalid syntax. !draft help for help.")

    async def rules(self, message: discord.message.Message, text):
        com, mantissa = text.split(" ")[0].lower().strip(), " ".join(text.split(" ")[1:])
        m = RulesModel(str(message.guild.id))
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
        print(f"Initiating draft on {message.guild.name}.")
        rm = RulesModel(str(message.guild.id))
        pm = PlayerModel(str(message.guild.id))
        om = PotModel(str(message.guild.id))
        
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
                            await u.send("\n- ".join(["Your options are:"] + [f"{i+1}. {o}" for i, o in enumerate(os)]))
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
                await message.channel.send("\n- ".join(["Draft step ready:"] + [f"{k}:\n  - {'\n  - '.join(v)}" for k, v in options.items()]))
            
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
        