from typeguard import typechecked
from typing import List
from tengine.preserve.preserver import *


class EnabledChannels(Preserver):
    def __init__(self, state_file_path: Path):
        super().__init__(state_file_path)

    @typechecked
    def is_enabled(self, str_channel_id: str):
        # assert type(str_channel_id) == str
        return str_channel_id in self.state

    @typechecked
    def get_channel_dict(self, str_channel_id: str):
        # assert type(str_channel_id) == str
        assert self.is_enabled(str_channel_id)
        return self.state[str_channel_id]

    def enabled_channel_ids(self) -> List[int]:
        str_arr = self.state.__dict__['_data'].keys()
        arr = [int(x) for x in str_arr]
        return arr
