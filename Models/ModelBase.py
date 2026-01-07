import json
from pathlib import Path
from typing import Optional, Union

from discord import Guild, VoiceChannel, StageChannel, TextChannel, ForumChannel, CategoryChannel, Thread, DMChannel, \
    GroupChannel

InteractionChannel = Union[
    VoiceChannel,
    StageChannel,
    TextChannel,
    ForumChannel,
    CategoryChannel,
    Thread,
    DMChannel,
    GroupChannel,
]

data_path = Path(__file__).parent.parent.joinpath('data').absolute()

class ModelBase:
    def __init__(self, guild: Guild, channel: Optional[InteractionChannel], file_name: str) -> None:
        self.guild = guild
        self.preset_path = data_path.joinpath("presets.json")
        self.cs_path = data_path.joinpath("city_states.json")
        if channel is None:
            if self.guild is None:
                self.path = data_path
            else:
                self.path = data_path.joinpath(f"{self.guild.id} - {self.guild.name}")
        else:
            self.path = data_path.joinpath(f"{self.guild.id} - {self.guild.name}", f"{channel.id} - {channel.name}")
        self.file_path = self.path.joinpath(f"{file_name}.json")
        if not self.path.exists():
            self.path.mkdir(parents=True)
        self.data = {}
        self._load_data()

    def _load_data(self) -> None:
        if not self.file_path.is_file():
            return self._no_data()
        with open(self.file_path, "r") as f:
            self.data = json.load(f)
    
    def _no_data(self) -> None:
        """Overwrite this method to handle no existing data file."""
        pass

    def _save_data(self) -> None:
        with open(self.file_path, "w") as f:
            f.write(json.dumps(self.data, indent=4))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save_data()