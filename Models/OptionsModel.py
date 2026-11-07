from datetime import datetime
from random import shuffle, seed
from typing import Optional

from discord import Guild, User

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
        return self.data['options'].copy()
    
    def get_bans(self) -> list[str]:
        if not 'bans' in self.data.keys():
            self.data['bans'] = []
        return self.data['bans'].copy()
    
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
        opts = self.get_options()
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
        self.remove_pot(option)
    
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
        seed(datetime.now().timestamp())
        shuffle(pot)
        return pot

    def get_shuffled_options(self, *exclude: str) -> list[str]:
        pot = self.get_unbanned_options()
        for e in exclude:
            try:
                pot.remove(e)
            except ValueError:
                pass
        seed(datetime.now().timestamp())
        shuffle(pot)
        return pot
    
    def clear_bans(self) -> None:
        self.data['bans'] = []
    
    def clear_pot(self) -> None:
        self.data['pot'] = []

    def update_auto_actions(self, user: User, bans: list[str], picks: list[str]):
        if not 'auto_actions' in self.data.keys():
            self.data['auto_actions'] = {}
        self.data['auto_actions'][str(user.id)] = {'bans': bans, 'picks': picks}

    def add_auto_ban(self, user: User, ban: str):
        if not 'auto_actions' in self.data.keys():
            self.data['auto_actions'] = {}
        if not str(user.id) in self.data['auto_actions'].keys():
            self.data['auto_actions'][str(user.id)] = {'bans': [], 'picks': []}
        if not ban in self.data['auto_actions'][str(user.id)]['bans']:
            self.data['auto_actions'][str(user.id)]['bans'].append(ban)

    def remove_auto_ban(self, user: User, ban: str):
        if not 'auto_actions' in self.data.keys():
            return
        if not str(user.id) in self.data['auto_actions'].keys():
            return
        try:
            self.data['auto_actions'][str(user.id)]['bans'].remove(ban)
        except ValueError:
            pass

    def add_auto_pick(self, user: User, pick: str):
        if not 'auto_actions' in self.data.keys():
            self.data['auto_actions'] = {}
        if not str(user.id) in self.data['auto_actions'].keys():
            self.data['auto_actions'][str(user.id)] = {'bans': [], 'picks': []}
        if not pick in self.data['auto_actions'][str(user.id)]['picks']:
            self.data['auto_actions'][str(user.id)]['picks'].append(pick)

    def remove_auto_pick(self, user: User, pick: str):
        if not 'auto_actions' in self.data.keys():
            return
        if not str(user.id) in self.data['auto_actions'].keys():
            return
        try:
            self.data['auto_actions'][str(user.id)]['picks'].remove(pick)
        except ValueError:
            pass

    def get_auto_actions(self, user: User) -> dict[str, list[str]]:
        if not 'auto_actions' in self.data.keys():
            return {}
        return self.data['auto_actions'].get(str(user.id), {})

    def get_valid_auto_ban(self, user) -> str|None:
        if not 'auto_actions' in self.data.keys():
            return None
        actions = self.data['auto_actions'].get(str(user.id), {})
        if not 'bans' in actions.keys():
            return None
        for ban in actions['bans']:
            if not ban in self.data['bans']:
                return ban
        return None

    def get_valid_auto_pick(self, user) -> str|None:
        if not 'auto_actions' in self.data.keys():
            return None
        actions = self.data['auto_actions'].get(str(user.id), {})
        if not 'picks' in actions.keys():
            return None
        for pick in actions['picks']:
            if not pick in self.data['pot'] and not pick in self.data['bans']:
                return pick
        return None

    def clear_auto_actions(self):
        self.data['auto_actions'] = {}