from typing import Optional, Union

from discord import ButtonStyle, Emoji, PartialEmoji
from discord.ui import Button


class BoolButton(Button):
    def __init__(
            self,
            *,
            starting_value: bool = False,
            label: Optional[str] = None,
            disabled: bool = False,
            custom_id: Optional[str] = None,
            url: Optional[str] = None,
            emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
            row: Optional[int] = None,
            sku_id: Optional[int] = None,
    ):
        super().__init__(
            style=ButtonStyle.red, 
            label=label, 
            disabled=disabled, 
            custom_id=custom_id, 
            url=url, 
            emoji=emoji, 
            row=row, 
            sku_id=sku_id
        )
        self.value = False
        if starting_value:
            self.toggle()
    
    def toggle(self):
        self.value = not self.value
        if self.value:
            self.style = ButtonStyle.green
        else:
            self.style = ButtonStyle.red
