import logging
import inject
from pathlib import Path
from typing import Dict

from liker.state.enabled_channels import EnabledChannels
from liker.state.channel_state import ChannelState

logger = logging.getLogger(__file__)


class SpaceState:
    enabled_channels = inject.attr(EnabledChannels)

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.channels: Dict[str, ChannelState] = {}

    def ensure_channel_state(self, channel_id) -> ChannelState:
        str_channel_id = str(channel_id)
        if str_channel_id not in self.channels:
            path = self.state_dir / f'{str_channel_id}.json'
            self.channels[str_channel_id] = ChannelState(path)
        return self.channels[str_channel_id]
