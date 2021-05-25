from typeguard import typechecked
from typing import List, Optional
from tengi.state.preserver import *
from tengi import telegram_bot_utils


class EnabledChannels(Preserver):
    def __init__(self, state_file_path: Path):
        super().__init__(state_file_path)

    @typechecked
    def is_enabled(self, str_channel_id: str):
        return str_channel_id in self.state

    @typechecked
    def get_channel_dict(self, str_channel_id: str) -> dict:
        assert self.is_enabled(str_channel_id)
        return self.state[str_channel_id]

    @typechecked
    def set_channel_dict(self, str_channel_id: str, channel_dict: dict):
        if not telegram_bot_utils.is_int_chat_id(str_channel_id):
            raise ValueError('str_channel_id should be a number')
        self.state[str_channel_id] = channel_dict

    @typechecked
    def update_channel_dict(self,
                            str_channel_id: str,
                            reactions: List[str],
                            linked_chat_id: Optional[int]):
        new_fields = {
            'reactions': reactions,
            'linked_chat_id': linked_chat_id
        }
        if self.is_enabled(str_channel_id):
            channel_dict = self.get_channel_dict(str_channel_id)
            channel_dict.update(new_fields)
        else:
            channel_dict = new_fields
        self.set_channel_dict(str_channel_id=str_channel_id, channel_dict=channel_dict)

    def disable_channel(self, str_channel_id: str):
        assert self.is_enabled(str_channel_id)
        with self.state:
            del self.state[str_channel_id]

    def enabled_channel_ids(self) -> List[int]:
        str_arr = self.state.__dict__['_data'].keys()
        arr = [int(x) for x in str_arr]
        return arr

    def try_get_channel_id_for_linked_chat_id(self, linked_chat_id) -> Optional[int]:
        result = None
        for ch_id in self.enabled_channel_ids():
            ch_dict = self.get_channel_dict(str(ch_id))
            if ch_dict['linked_chat_id'] == linked_chat_id:
                result = ch_id
                break
        return result
