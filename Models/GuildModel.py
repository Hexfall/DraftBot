import json

from discord import Guild

from Models.ModelBase import ModelBase


class GuildModel(ModelBase):
    def __init__(self, guild: Guild) -> None:
        super().__init__(guild, None, "defaults")
    
    def get_options(self) -> list[str]:
        if not "default_options" in self.data.keys():
            self.data["default_options"] = []
            self._save_data()
        return self.data["default_options"]

    def get_presets(self) -> dict[str, list[str]]:
        if not "presets" in self.data.keys():
            with open(self.preset_path, "r") as f:
                self.data["presets"] = json.load(f)
        return self.data["presets"]
    
    def get_preset_names(self) -> list[str]:
        return list(self.get_presets().keys())
    
    def use_preset(self, name: str):
        presets = self.get_presets()
        if not name in presets.keys():
            print(f"Preset '{name}' not found.")
            return
        self.data["default_options"] = sorted(presets[name], key=lambda x: x.lower())
    
    def add_option(self, option: str):
        if not option in self.get_default_options():
            self.data["default_options"].append(option)
            self.data["default_options"].sort(key=lambda x: x.lower())
    
    def remove_option(self, option: str):
        try:
            self.data["default_options"].remove(option)
        except ValueError:
            pass
    