import json
from pathlib import Path

data_path = Path(__file__).parent.parent.joinpath('data').absolute()

class ModelBase:
    def __init__(self, guild: str, file_name: str) -> None:
        self.guild = guild
        self.path = data_path.joinpath(self.guild)
        self.file_path = self.path.joinpath(file_name + ".json")
        if not self.path.exists():
            self.path.mkdir(parents=True)
        self.data = []
        self._load_data()

    def _load_data(self):
        if not self.file_path.is_file():
            return
        with open(self.file_path, "r") as f:
            self.data = json.load(f)

    def _save_data(self):
        with open(self.file_path, "w") as f:
            f.write(json.dumps(self.data, indent=4))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save_data()