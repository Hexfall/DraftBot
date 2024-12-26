import json

from Models.ModelBase import ModelBase


class PlayerModel(ModelBase):
    def __init__(self, guild: str):
        super().__init__(guild)
        self.players = []
        self.__load_data()

    def __load_data(self):
        if not self.path.joinpath("players.json").is_file():
            return
        with open(self.path.joinpath("players.json")) as f:
            self.players = json.load(f)
    
    def __save_data(self):
        with open(self.path.joinpath("players.json"), "w") as f:
            f.write(json.dumps(self.players, indent=4))
    
    def add_player(self, player: str) -> None:
        if player in self.players:
            return
        self.players.append(player)
        self.__save_data()
    
    def rem_player(self, player: str) -> None:
        if player in self.players:
            self.players.remove(player)
            self.__save_data()
    
    def clear_players(self):
        self.players = []
        self.__save_data()
        