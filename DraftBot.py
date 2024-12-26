import discord

from Models.PlayerModel import PlayerModel
from Models.PotModel import PotModel

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
            await message.channel.send('\n- '.join(["Players currently in draft:"] + m.data))
        elif com == "add":
            for p in mantissa.split():
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
            await message.channel.send('\n- '.join(["Options currently in pot:"] + m.data))
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
