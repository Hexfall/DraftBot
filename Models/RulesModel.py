from Models.ModelBase import ModelBase


class RulesModel(ModelBase):
    def __init__(self, guild: str):
        super().__init__(guild, "rules")
        if not self.data:
            self.data = {
                "mulligans": True,
                "options": 3,
            }
    
    def set_mulligans(self, mulligans: bool):
        self.data["mulligans"] = mulligans
        self._save_data()
    
    def set_options(self, options: int):
        self.data["options"] = options
        self._save_data()
        