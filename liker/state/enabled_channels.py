import logging
from tengine.preserve.preserver import *


class EnabledChannels(Preserver):
    def __init__(self, state_file_path: Path):
        super().__init__(state_file_path)

    def is_enabled(self, channel_id):
        str_channel_id = str(channel_id)
        return str_channel_id in self.state

    def get_channel_dict(self, channel_id):
        assert self.is_enabled(channel_id)
        str_channel_id = str(channel_id)
        return self.state[str_channel_id]

    def enabled_channel_ids(self):
        str_arr = self.state.__dict__['_data'].keys()
        arr = [int(x) for x in str_arr]
        return arr
