from pathlib import Path
import inject
from tengi.state.timed_preserver import TimedPreserver
from tengi import Config

from liker.state.reaction_hashes import ReactionHashes
from liker.state.markup_queue import MarkupQueue
from liker.state.markup_trail import MarkupTrail
from liker.state.comment_trail import CommentTrail


class ChannelState(TimedPreserver):
    config = inject.attr(Config)

    def __init__(self, state_dir: Path, str_channel_id: str):
        state_path = state_dir / f'{str_channel_id}.json'
        save_period = self.config['channel_state_save_seconds']
        super().__init__(state_path, save_period=save_period)

        last_reactions_path = state_dir / f'{str_channel_id}_last_reactions.json'
        self.last_reactions = ReactionHashes(last_reactions_path)

        self.markup_queue = MarkupQueue(self.state)
        self.markup_trail = MarkupTrail(self.state)
        self.comment_trail = CommentTrail(self.state)

    def update(self):
        super().update()
        self.last_reactions.update()
