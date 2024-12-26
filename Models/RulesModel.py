from Models.ModelBase import ModelBase


class RulesModel(ModelBase):
    def __init__(self, guild: str):
        super().__init__(guild, "rules")
        if not self.data:
            self.data = {
                "mulligans": True,
                "options": 3,
                "public": True,
            }
    
    def set_mulligans(self, mulligans: bool):
        self.data["mulligans"] = mulligans
        self._save_data()
    
    def set_options(self, options: int):
        if options < 1:
            raise ValueError("Options must be greater than 0")
        self.data["options"] = options
        self._save_data()
    
    def set_public(self, public: bool):
        self.data["public"] = public
        self._save_data()
        