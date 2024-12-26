import json
from pathlib import Path

data_path = Path(__file__).parent.parent.joinpath('data')

class ModelBase:
    def __init__(self, guild: str) -> None:
        self.guild = guild
        self.path = data_path.joinpath(self.guild)
        if not self.path.exists():
            self.path.mkdir(parents=True)