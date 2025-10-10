from random import shuffle
from typing import Optional

from discord import Guild

from Models.GuildModel import GuildModel
from Models.ModelBase import ModelBase, InteractionChannel


class OptionsModel(ModelBase):
    def __init__(self, guild: Guild, channel: Optional[InteractionChannel]):
        super().__init__(guild, channel, "pot")

    def _no_data(self) -> None:
        with GuildModel(self.guild) as guild_model:
            self.data['options'] = guild_model.get_options()
        self._save_data()
    
    def get_options(self) -> list[str]:
        if not 'options' in self.data.keys():
            self._no_data()
        return self.data['options']
    
    def get_bans(self) -> list[str]:
        if not 'bans' in self.data.keys():
            self.data['bans'] = []
        return self.data['bans']
    
    def get_pot(self, *exclude: str) -> list[str]:
        if not 'pot' in self.data.keys():
            self.data['pot'] = []
        pot = self.data['pot'].copy()
        for e in exclude:
            try:
                pot.remove(e)
            except ValueError:
                pass
        return pot
    
    def get_unbanned_options(self) -> list[str]:
        opts = self.get_options().copy()
        for ban in self.get_bans():
            try:
                opts.remove(ban)
            except ValueError:
                pass
        return opts

    def get_presets(self) -> dict[str, list[str]]:
        with GuildModel(self.guild) as guild_model:
            return guild_model.get_presets()

    def get_preset_names(self) -> list[str]:
        return list(self.get_presets().keys())

    def use_preset(self, name: str):
        presets = self.get_presets()
        if not name in presets.keys():
            print(f"Preset '{name}' not found.")
            return
        self.data["options"] = sorted(presets[name], key=lambda x: x.lower())

    def add_option(self, option: str):
        if not option in self.get_options():
            self.data["options"].append(option)
            self.data["options"].sort(key=lambda x: x.lower())

    def remove_option(self, option: str):
        try:
            self.data["options"].remove(option)
        except ValueError:
            pass
    
    def add_ban(self, option: str):
        if not option in self.get_bans():
            self.data["bans"].append(option)
    
    def remove_ban(self, option: str):
        self.get_bans() # Ensure 'bans' exists
        try:
            self.data["bans"].remove(option)
        except ValueError:
            pass
    
    def add_pot(self, option: str):
        self.get_pot() # Ensure 'pot' exists 
        self.data['pot'].append(option)
    
    def remove_pot(self, option: str):
        self.get_pot() # Ensure 'pot' exists
        try:
            self.data['pot'].remove(option)
        except ValueError:
            pass
    
    def get_available_add_options(self) -> list[str]:
        l = self.get_unbanned_options().copy()
        for opt in self.get_pot():
            try:
                l.remove(opt)
            except ValueError:
                pass
        return l
    
    def get_shuffled_pot(self, *exclude: str) -> list[str]:
        pot = self.get_pot(*exclude)
        shuffle(pot)
        return pot