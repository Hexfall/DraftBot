import discord
from discord import Interaction
from discord.ui import View

from Views.UserOptionChoiceView import UserOptionChoiceView


class DraftPickView(View):
    def __init__(self, user: discord.Member, options: list[str]):
        super().__init__()
        self.user = user
        self.option_select = UserOptionChoiceView(self, options + ["Mulligan"], row=1)
        self.option_select.callback = self.__callback
    
    async def __callback(self, interaction: Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This isn't your pick. Wait your turn.", ephemeral=True)
            return
        await self.callback(interaction, self.option_select.get_option())
    
    async def callback(self, interaction: Interaction, option: str):
        pass
        