import json
from random import shuffle

from discord import Guild

from Models.ModelBase import ModelBase


class CityStateModel(ModelBase):
    def __init__(self, guild: Guild):
        super().__init__(guild, None, "city_states")

    def _no_data(self) -> None:
        with open(self.cs_path) as f:
            self.data = json.load(f)
            
    def _load_data(self) -> None:
        # File should never exist. Skip straight to getting default.
        self._no_data()
    
    def _save_data(self) -> None:
        # City states should be immutable.
        pass
    
    def get_type(self, city_state: str) -> str:
        for k, v in self.data.items():
            if city_state in v:
                return k
        raise ValueError(f"{city_state} is not a valid city state.")
    
    def get_city_states(self, amount: int) -> dict[str, list[str]]:
        """Returns a dictionary of `amount` unique city states."""
        options = []
        for v in self.data.values():
            options.extend(v)
        shuffle(options)
        
        ret = dict([(k, []) for k in self.data.keys()])
        for cs in options[:amount]:
            type = self.get_type(cs)
            ret[type] = sorted(ret[type] + [cs])
        
        return ret
    
    def get_city_states_by_type(self, cul: int = 2, ind: int = 2, mil: int = 2, rel: int = 2, sci: int = 2, tra: int = 2) -> dict[str, list[str]]:
        """Returns a dictionary of unique city states of the specified types."""
        ret = {}
        amounts = [cul, ind, mil, rel, sci, tra]
        types = sorted(list(self.data.keys()))
        for t, a in zip(types, amounts):
            if t in self.data.keys():
                category_options = list(self.data[t])
                shuffle(category_options)
                ret[t] = sorted(category_options[:a])
        return ret


if __name__ == "__main__":
    # Test
    model = CityStateModel(None)
    print(model.get_city_states(10))
    print(model.get_city_states_by_type())