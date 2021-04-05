import logging
import inject
from jsonstore import JsonStore
from typing import Optional
from typeguard import typechecked
from tengine import Config

logger = logging.getLogger(__file__)


class CommentTrail:
    config = inject.attr(Config)

    def __init__(self, state: JsonStore):
        self.state = state

    def ensure_trail(self):
        if 'comment_trail' not in self.state:
            self.state['comment_trail'] = {}
        return self.state['comment_trail']

    def update_trail(self, trail):
        self.state['comment_trail'] = trail

    @typechecked
    def add(self, str_message_id: str, comment_dict: dict):
        trail = self.ensure_trail()
        if str_message_id in trail:
            del trail[str_message_id]
        trail_max_len = self.config['comment_trail']
        trail_items = [(str_message_id, comment_dict)] + list(trail.items())
        trail_items = trail_items[:trail_max_len]
        trail = dict(trail_items)
        self.update_trail(trail)

    @typechecked
    def try_get(self, str_message_id: str) -> Optional[dict]:
        trail = self.ensure_trail()
        comment_dict = trail.get(str_message_id, None)
        return comment_dict
