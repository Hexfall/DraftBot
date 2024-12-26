from Models.ModelBase import ModelBase


class PotModel(ModelBase):
    def __init__(self, guild: str):
        super().__init__(guild, "pot")
    
    def add_pot(self, element: str):
        if not element in self.data and not element.lower() == "mulligan":
            self.data.append(element)
            self._save_data()
    
    def rem_pot(self, element: str):
        if element in self.data:
            self.data.remove(element)
            self._save_data()
    
    def clear_pot(self):
        self.data.clear()
        self._save_data()
