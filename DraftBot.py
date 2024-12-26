import discord


PREFIX = "!draft"

class DraftBot(discord.Client):
    def __init__(self, intents: discord.Intents = discord.Intents.default()):
        super().__init__(intents=intents)
        self.paths = {
            "help": help
        }
    
    async def on_ready(self):
        print('Logged in as: {0} {1}'.format(self.user.name, self.user.id))
    
    async def on_message(self, message: discord.message.Message):
        if message.author == self.user:
            return
        
        if message.content.startswith(PREFIX):
            await self.parse_message(message, message.content[len(PREFIX):].strip())

    async def parse_message(self, message: discord.message.Message, command):
        try:
            com, mantissa = command.split(" ")[0], " ".join(command.split(" ")[1:])
            await getattr(self, com.lower().strip())(message, mantissa)
        except AttributeError:
            await message.channel.send("Invalid syntax. !draft help for help.")
    
    async def help(self, message: discord.message.Message, command):
        await message.channel.send("Idk man, figure it out.")
    
    async def echo(self, message: discord.message.Message, text):
        await message.channel.send(f"`{text}`")
        
    async def ping(self, message: discord.message.Message, text):
        await message.channel.send(message.author.mention)
        await message.channel.send(message.guild.name)
