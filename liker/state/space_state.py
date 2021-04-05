import logging
import inject
from pathlib import Path
from typing import Dict
from typeguard import typechecked

from liker.state.enabled_channels import EnabledChannels
from liker.state.channel_state import ChannelState

logger = logging.getLogger(__file__)


class SpaceState:
    enabled_channels = inject.attr(EnabledChannels)

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.channels: Dict[str, ChannelState] = {}

    @typechecked
    def ensure_channel_state(self, str_channel_id: str) -> ChannelState:
        if str_channel_id not in self.channels:
            self.channels[str_channel_id] = ChannelState(state_dir=self.state_dir,
                                                         str_channel_id=str_channel_id)
        return self.channels[str_channel_id]
