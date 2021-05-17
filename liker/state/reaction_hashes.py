import inject
from tengi import Config
from tengi.state.timed_preserver import *


class ReactionHashes(TimedPreserver):
    config = inject.attr(Config)

    def __init__(self, state_file_path: Path):
        save_period = self.config['last_reactions_save_seconds']
        super().__init__(state_file_path, save_period=save_period)

    def has(self, reaction_hash: str) -> bool:
        if 'hashes' not in self.state:
            return False

        hashes = self.state['hashes']
        return reaction_hash in hashes

    def save(self, hashes):
        n_to_keep = self.config['last_reactions']
        hashes = hashes[:n_to_keep]
        self.state['hashes'] = hashes

    def add(self, reaction_hash: str):
        if 'hashes' not in self.state:
            self.state['hashes'] = []
        hashes = self.state['hashes']
        hashes.insert(0, reaction_hash)
        self.save(hashes)

    def remove(self, reaction_hash: str):
        if 'hashes' not in self.state:
            return
        hashes = self.state['hashes']
        hashes = [x for x in hashes if x != reaction_hash]
        self.save(hashes)
