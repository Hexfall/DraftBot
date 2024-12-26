import json

from Models.ModelBase import ModelBase


class PlayerModel(ModelBase):
    def __init__(self, guild: str):
        super().__init__(guild, "players")
    
    def add_player(self, player: str) -> None:
        if player in self.data:
            return
        self.data.append(player)
        self._save_data()
    
    def rem_player(self, player: str) -> None:
        if player in self.data:
            self.data.remove(player)
            self._save_data()
    
    def clear_players(self):
        self.data = []
        self._save_data()
        