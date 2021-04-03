import inject
import time
import logging
from tengine import Config, TelegramBot

from liker.state.enabled_channels import EnabledChannels
from liker.state.space_state import SpaceState
from liker.button import markup_utils
from liker.setup import constants

logger = logging.getLogger(__file__)


class MarkupSyncQueue:
    """
    Handles Telegram message update limits
        https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
        30 messages per second
        20 messages per minute to the same group
    State of the queue is stored in the RAM as it's not critical to us to loose this queue in case of bot restart,
        we'll sync message reaction with the first future user reqction.
    """
    config = inject.attr(Config)
    telegram_bot = inject.attr(TelegramBot)
    enabled_channels = inject.attr(EnabledChannels)
    space_state = inject.attr(SpaceState)

    def __init__(self):
        self.channel_queues = {}
        self.channel_update_times = {}

    def add(self, channel_id, message_id, to_top=False):
        ch_queue = self._ensure_channel_queue(channel_id)

        if to_top:
            if message_id in ch_queue:
                ch_queue.remove(message_id)
            ch_queue.insert(0, message_id)
        elif message_id not in ch_queue:
            ch_queue.append(message_id)

    def _ensure_channel_queue(self, channel_id) -> list:
        if channel_id not in self.channel_queues:
            self.channel_queues[channel_id] = []
        return self.channel_queues[channel_id]

    def _ensure_channel_update_times(self, channel_id) -> list:
        if channel_id not in self.channel_update_times:
            self.channel_update_times[channel_id] = []
        return self.channel_update_times[channel_id]

    def update(self):
        # Clear state from potentially disabled channels
        enabled_channel_ids = self.enabled_channels.enabled_channel_ids()
        for state_dict in [self.channel_queues, self.channel_update_times]:
            for ch_id in list(state_dict.keys()):
                if ch_id not in enabled_channel_ids:
                    del state_dict[ch_id]

        # TODO: implement global limit from self.config['global_rate_per_second'] to manage load from multiple
        #   channels. Will be a problem in case of >100-200 channels connected to the bot
        cur_time = time.time()

        rate_per_minute = self.config['channel_rate_per_minute']
        rate_avg_seconds = 60 / rate_per_minute
        rate_min_seconds = self.config['channel_rate_min_seconds']
        rate_span = 2 * (rate_avg_seconds - rate_min_seconds)
        rate_span = max(rate_span, 0)

        for ch_id in self.channel_queues:
            try:
                upd_times = self._ensure_channel_update_times(ch_id)
                upd_times = [x for x in upd_times if (cur_time - x <= 60) and (cur_time >= x)]
                # If there was no updates in the channel last minute -- consume half a minute
                dt_to_consume = 30 if (not upd_times) else (cur_time - max(upd_times))

                ch_queue = self._ensure_channel_queue(ch_id)
                while ch_queue:
                    # If we made 'rate_per_minute' updates per last minute -- don't send more updates
                    if len(upd_times) >= rate_per_minute:
                        break

                    # Make elastic delay time
                    slowdown_factor = len(upd_times) / rate_per_minute
                    cur_timeout = rate_min_seconds + slowdown_factor * rate_span
                    if cur_timeout > dt_to_consume:
                        break

                    m_id = ch_queue.pop(0)

                    # Don't sync the reply markup that is already synced
                    if not self._is_reply_markup_synced(channel_id=ch_id, message_id=m_id):
                        dt_to_consume -= cur_timeout
                        upd_times.append(cur_time)
                        self._sync_message_reply_markup(channel_id=ch_id, message_id=m_id)

                self.channel_update_times[ch_id] = upd_times
            except Exception as ex:
                logger.exception(ex)

    def _is_reply_markup_synced(self, channel_id, message_id):
        channel_state = self.space_state.ensure_channel_state(channel_id)
        return channel_state.are_reactions_synced(message_id)

    def _sync_message_reply_markup(self, channel_id, message_id):
        # Check for reactions to be synced as Telegram rises an exception in case reactions
        if self._is_reply_markup_synced(channel_id=channel_id, message_id=message_id):
            return

        channel_state = self.space_state.ensure_channel_state(channel_id)
        # Check for reactions to be synced as Telegram rises an exception in case reactions
        channel_dict = self.enabled_channels.get_channel_dict(channel_id)
        enabled_reactions = channel_dict['reactions']
        message_dict = channel_state.try_get_message_dict(message_id)
        reply_markup = markup_utils.build_reply_markup(enabled_reactions=enabled_reactions,
                                                       state_dict=message_dict,
                                                       handler=constants.BUTTON_HANDLER,
                                                       case_id='')

        self.telegram_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                        message_id=message_id,
                                                        reply_markup=reply_markup)
        channel_state.mark_reactions_synced(message_id)
