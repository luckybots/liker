import logging
from typing import Optional
import inject
from tengine import Config
from tengine.preserve.preserver import *

logger = logging.getLogger(__file__)


class ChannelState(Preserver):
    config = inject.attr(Config)

    def __init__(self, state_file_path: Path):
        super().__init__(state_file_path)

    def has_message(self, message_id):
        str_message_id = str(message_id)
        return str_message_id in self.state

    def try_get_message_dict(self, message_id) -> Optional[dict]:
        str_message_id = str(message_id)
        result = self.state[str_message_id] if (str_message_id in self.state) else None
        return result

    def ensure_message_dict(self, message_id) -> dict:
        str_message_id = str(message_id)
        if str_message_id not in self.state:
            self.state[str_message_id] = {}
        return self.state[str_message_id]

    def update_message_dict(self, message_id, message_dict):
        self.state[str(message_id)] = message_dict

    def change_reaction_counter(self, message_id, r, delta):
        message_dict = self.ensure_message_dict(message_id)

        if 'reactions' not in message_dict:
            message_dict['reactions'] = {}
        reactions = message_dict['reactions']

        if r not in reactions:
            reactions[r] = 0
        reactions[r] += delta

        self.update_message_dict(message_id=message_id, message_dict=message_dict)

    def mark_reactions_synced(self, message_id):
        message_dict = self.ensure_message_dict(message_id)
        if 'reactions' in message_dict:
            message_dict['synced_reactions'] = message_dict['reactions'].copy()
            self.update_message_dict(message_id=message_id, message_dict=message_dict)

    def are_reactions_synced(self, message_id):
        message_dict = self.ensure_message_dict(message_id)
        reactions = message_dict.get('reactions', None)
        synced_reactions = message_dict.get('synced_reactions', None)
        result = (reactions is not None) and (reactions == synced_reactions)
        return result

    def has_reaction_hash(self, reaction_hash: str) -> bool:
        if '__last_reaction_hashes' not in self.state:
            return False

        last_reaction_hashes = self.state['__last_reaction_hashes']
        return reaction_hash in last_reaction_hashes

    def save_last_reaction_hashes(self, last_reaction_hashes):
        n_to_keep = self.config['last_reactions']
        last_reaction_hashes = last_reaction_hashes[:n_to_keep]
        self.state['__last_reaction_hashes'] = last_reaction_hashes

    def add_reaction_hash(self, reaction_hash: str):
        if '__last_reaction_hashes' not in self.state:
            self.state['__last_reaction_hashes'] = []
        last_reaction_hashes = self.state['__last_reaction_hashes']
        last_reaction_hashes.insert(0, reaction_hash)
        self.save_last_reaction_hashes(last_reaction_hashes)

    def remove_reaction_hash(self, reaction_hash: str):
        if '__last_reaction_hashes' not in self.state:
            return
        last_reaction_hashes = self.state['__last_reaction_hashes']
        last_reaction_hashes = [x for x in last_reaction_hashes if x != reaction_hash]
        self.save_last_reaction_hashes(last_reaction_hashes)
