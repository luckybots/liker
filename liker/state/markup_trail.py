import logging
import inject
from jsonstore import JsonStore
from typing import Optional
from typeguard import typechecked
from tengi import Config

logger = logging.getLogger(__file__)


class MarkupTrail:
    config = inject.attr(Config)

    def __init__(self, state: JsonStore):
        self.state = state

    def ensure_trail(self):
        if 'markup_trail' not in self.state:
            self.state['markup_trail'] = {}
        return self.state['markup_trail']

    def update_trail(self, trail):
        self.state['markup_trail'] = trail

    @typechecked
    def add(self, str_message_id: str, str_markup: str):
        trail = self.ensure_trail()
        if str_message_id in trail:
            del trail[str_message_id]
        trail_max_len = self.config['reply_markup_trail']
        trail_items = [(str_message_id, str_markup)] + list(trail.items())
        trail_items = trail_items[:trail_max_len]
        trail = dict(trail_items)
        self.update_trail(trail)

    @typechecked
    def try_get(self, str_message_id: str) -> Optional[str]:
        trail = self.ensure_trail()
        str_markup = trail.get(str_message_id, None)
        return str_markup
