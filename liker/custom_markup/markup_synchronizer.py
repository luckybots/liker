import inject
import time
import logging
from telebot.apihelper import ApiTelegramException
from typing import Optional
from telebot.types import InlineKeyboardMarkup
from tengi import Config, TelegramBot, telegram_error

from liker.state.enabled_channels import EnabledChannels
from liker.state.space_state import SpaceState

logger = logging.getLogger(__file__)


class MarkupSynchronizer:
    """
    Handles Telegram message update limits
        https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
        30 messages per second
        20 messages per minute to the same group
    State of the queue is stored in channel states and thus persisted
    """
    config = inject.attr(Config)
    telegram_bot = inject.attr(TelegramBot)
    enabled_channels = inject.attr(EnabledChannels)
    space_state = inject.attr(SpaceState)

    def __init__(self):
        self.channel_update_times = {}

    def add(self, channel_id: int, message_id: int, reply_markup: InlineKeyboardMarkup, to_top=False):
        channel_state = self.space_state.ensure_channel_state(str(channel_id))
        str_reply_markup = reply_markup.to_json()
        channel_state.markup_queue.add(str_message_id=str(message_id),
                                       str_markup=str_reply_markup,
                                       to_top=to_top)

    def try_remove(self, channel_id: int, message_id: int):
        channel_state = self.space_state.ensure_channel_state(str(channel_id))
        channel_state.markup_queue.try_remove(str(message_id))

    def try_get_markup(self, channel_id: int, message_id: int) -> Optional[InlineKeyboardMarkup]:
        channel_state = self.space_state.ensure_channel_state(str(channel_id))
        str_reply_markup = channel_state.markup_queue.try_get(str(message_id))
        reply_markup = None if (str_reply_markup is None) else InlineKeyboardMarkup.de_json(str_reply_markup)
        return reply_markup

    def _ensure_channel_update_times(self, channel_id: int) -> list:
        if channel_id not in self.channel_update_times:
            self.channel_update_times[channel_id] = []
        return self.channel_update_times[channel_id]

    def update(self):
        enabled_channel_ids = self.enabled_channels.enabled_channel_ids()

        # TODO: implement global limit from self.config['global_rate_per_second'] to manage load from multiple
        #   channels. Will be a problem in case of >100-200 channels connected to the bot
        cur_time = time.time()

        rate_per_minute = self.config['channel_rate_per_minute']
        rate_avg_seconds = 60 / rate_per_minute
        rate_min_seconds = self.config['channel_rate_min_seconds']
        rate_span = 2 * (rate_avg_seconds - rate_min_seconds)
        rate_span = max(rate_span, 0)

        for ch_id in enabled_channel_ids:
            try:
                upd_times = self._ensure_channel_update_times(ch_id)
                upd_times = [x for x in upd_times if (cur_time - x <= 60) and (cur_time >= x)]
                # If there was no updates in the channel last minute -- consume half a minute
                dt_to_consume = 30 if (not upd_times) else (cur_time - max(upd_times))

                ch_state = self.space_state.ensure_channel_state(str(ch_id))
                ch_queue = ch_state.markup_queue.ensure_queue()
                while ch_queue:
                    m_id_str = None
                    reply_markup_str = None
                    try:
                        m_id_str = list(ch_queue.keys())[0]

                        # Handle channel being disabled during the iteration -- could happen in case bot was
                        # removed from the channel
                        if not self.enabled_channels.is_enabled(str(ch_id)):
                            logger.info(f'Channel was disabled, ignoring {len(ch_queue):,} markups in the queue')
                            ch_queue = {}
                            break

                        reply_markup_str = ch_queue[m_id_str]

                        # If we made 'rate_per_minute' updates per last minute -- don't send more updates
                        if len(upd_times) >= rate_per_minute:
                            break

                        # Make elastic delay time
                        slowdown_factor = len(upd_times) / rate_per_minute
                        cur_timeout = rate_min_seconds + slowdown_factor * rate_span
                        logger.debug(f'queue timeout: {cur_timeout}')
                        if cur_timeout > dt_to_consume:
                            break

                        m_id = int(m_id_str)

                        reply_markup = InlineKeyboardMarkup.de_json(reply_markup_str)

                        dt_to_consume -= cur_timeout
                        upd_times.append(cur_time)

                        self.telegram_bot.bot.edit_message_reply_markup(chat_id=ch_id,
                                                                        message_id=m_id,
                                                                        reply_markup=reply_markup)
                        logger.debug(f'Markup synchronized for chat_id={ch_id}, message_id={m_id}')
                    # We don't break loop for all exceptions except TOO_MANY_REQUESTS to avoid infinite error loop
                    except ApiTelegramException as ex:
                        if ex.error_code == telegram_error.TOO_MANY_REQUESTS:
                            logger.error(f'Got TOO_MANY_REQUESTS error, will skip current channel update: {ex}')
                            break
                        elif (ex.error_code == telegram_error.BAD_REQUEST) and ('are exactly the same' in str(ex)):
                            # Error: Bad Request: message is not modified: specified new message content and reply
                            #   markup are exactly the same as a current content and reply markup of the message"
                            logger.warning(f'Cannot sync markup, chat_id={ch_id}, message_id={m_id_str}. {ex}')
                        elif (ex.error_code == telegram_error.BAD_REQUEST) and \
                                ('''message can't be edited''' in str(ex)):
                            # Error: Bad Request: message can't be edited
                            logger.warning(f'Bot does not have post edit rights, chat_id={ch_id}, '
                                           f'message_id={m_id_str}. {ex}')
                        elif ex.error_code == telegram_error.FORBIDDEN:
                            logger.warning(f'Bot was removed from the channel but tries to synchronize markup: '
                                           f'chat_id={ch_id}, message_id={m_id_str}. {ex}')
                            self.enabled_channels.disable_channel(str(ch_id))
                        else:
                            logger.exception(f'chat_id={ch_id}, message_id={m_id_str}\n{ex}')
                    except Exception as ex:
                        logger.exception(f'chat_id={ch_id}, message_id={m_id_str}\n{ex}')

                    # We delete markup from the queue only after it's synchronized
                    if m_id_str is not None:
                        if reply_markup_str is not None:
                            ch_state.markup_trail.add(str_message_id=m_id_str,
                                                      str_markup=reply_markup_str)
                        del ch_queue[m_id_str]

                self.channel_update_times[ch_id] = upd_times
                ch_state.markup_queue.update_queue(ch_queue)
            except Exception as ex:
                logger.exception(ex)
