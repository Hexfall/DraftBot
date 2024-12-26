#!/usr/bin/python
import discord
import DraftBot


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

def main() -> None:
    bot = DraftBot.DraftBot(intents=intents)
    bot.run(get_token())

def get_token() -> str:
    with open('token.txt', 'r') as file:
        return file.read().strip()

if __name__ == '__main__':
    main()