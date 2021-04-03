import logging
import inject
from telebot.apihelper import ApiTelegramException
from tengine import Config, TelegramBot, telegram_utils, Hasher, AbuseDetector
from tengine.telegram.inbox_handler import *

from liker.state.space_state import SpaceState
from liker.state.enabled_channels import EnabledChannels
from liker.button.markup_sync_queue import MarkupSyncQueue
from liker.setup import constants

logger = logging.getLogger(__file__)


class ButtonHandler(TelegramInboxHandler):
    config = inject.attr(Config)
    hasher = inject.attr(Hasher)
    telegram_bot = inject.attr(TelegramBot)
    enabled_channels = inject.attr(EnabledChannels)
    space_state = inject.attr(SpaceState)
    markup_sync_queue = inject.attr(MarkupSyncQueue)
    abuse_detector = inject.attr(AbuseDetector)

    def channel_post(self, channel_post: types.Message) -> bool:
        channel_id = channel_post.chat.id
        if not self.enabled_channels.is_enabled(channel_id):
            return False

        message_id = channel_post.id
        self.markup_sync_queue.add(channel_id=channel_id, message_id=message_id, to_top=True)
        return True

    def callback_query(self, callback_query: types.CallbackQuery) -> bool:
        handler, _case_id, reaction = telegram_utils.decode_button_data(callback_query.data)
        if handler != constants.BUTTON_HANDLER:
            return False

        if callback_query.message is None:
            return False

        chat_id = callback_query.message.chat.id
        if not self.enabled_channels.is_enabled(chat_id):
            return False

        sender_id = callback_query.from_user.id
        abuse_cool_down = self.abuse_detector.check_abuse(sender_id)
        if abuse_cool_down is not None:
            logger.warning(f'Abuse detected: {self.hasher.trimmed(sender_id)}')
            return True

        channel_id = chat_id
        message_id = callback_query.message.id
        reaction_id = f'{chat_id}_{message_id}_{sender_id}_{reaction}'
        reaction_hash = self.hasher.trimmed(reaction_id, hash_bytes=constants.REACTION_HASH_BYTES)

        channel_state = self.space_state.ensure_channel_state(channel_id)
        if channel_state.has_reaction_hash(reaction_hash):
            channel_state.change_reaction_counter(message_id=message_id, r=reaction, delta=-1)
            channel_state.remove_reaction_hash(reaction_hash)
            response_to_user = self.config['response_reaction_removed'].format(reaction)
        else:
            channel_state.change_reaction_counter(message_id=message_id, r=reaction, delta=1)
            channel_state.add_reaction_hash(reaction_hash)
            response_to_user = self.config['response_reaction_added'].format(reaction)

        self.markup_sync_queue.add(channel_id=channel_id, message_id=message_id)

        try:
            self.telegram_bot.answer_callback_query(callback_query.id, text=response_to_user)
        except ApiTelegramException as ex:
            logger.info(f'Cannot answer callback query, most likely it is expired: {ex}')

        return True
