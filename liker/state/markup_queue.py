import logging
from typing import Optional
from typeguard import typechecked
from jsonstore import JsonStore

logger = logging.getLogger(__file__)


class MarkupQueue:
    def __init__(self, state: JsonStore):
        self.state = state

    def ensure_queue(self) -> dict:
        if 'markup_queue' not in self.state:
            self.state['markup_queue'] = {}
        return self.state['markup_queue']

    def update_queue(self, markup_queue: dict):
        self.state['markup_queue'] = markup_queue

    @typechecked
    def add(self, str_message_id: str, str_markup: str, to_top: bool):
        queue = self.ensure_queue()
        if to_top:
            if str_message_id in queue:
                del queue[str_message_id]
            queue = dict([(str_message_id, str_markup)] + list(queue.items()))
        else:
            queue[str_message_id] = str_markup
        self.update_queue(queue)

    @typechecked
    def try_remove(self, str_message_id: str):
        queue = self.ensure_queue()
        if str_message_id in queue:
            del queue[str_message_id]
            self.update_queue(queue)

    @typechecked
    def try_get(self, str_message_id: str) -> Optional[str]:
        queue = self.ensure_queue()
        str_markup = queue.get(str_message_id, None)
        return str_markup
