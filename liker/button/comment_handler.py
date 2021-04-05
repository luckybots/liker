import logging
import inject
from telebot.types import InlineKeyboardMarkup
from tengine import telegram_utils
from tengine.telegram.inbox_handler import *
from tengine.telegram.constants import TELEGRAM_USER_ID

from liker.state.enabled_channels import EnabledChannels
from liker.state.space_state import SpaceState
from liker.button import markup_utils
from liker.button.markup_synchronizer import MarkupSynchronizer

logger = logging.getLogger(__file__)


class CommentHandler(TelegramInboxHandler):
    enabled_chats = inject.attr(EnabledChannels)
    space_state = inject.attr(SpaceState)
    markup_synchronizer = inject.attr(MarkupSynchronizer)

    def message(self, message: types.Message) -> bool:
        if not telegram_utils.is_group_message(message):
            return False

        if self._check_forward_from_channel(message):
            return True

        # TODO: handle replies
        # In replies to messages
        # reply_to_message.forward_from_chat.id = ? -1001380133596
        # reply_to_message.forward_from_message_id = 99
        # print('Point #1')
        # print(message)
        return False

    def _check_forward_from_channel(self, message: types.Message) -> bool:
        if message.from_user.id != TELEGRAM_USER_ID:
            logger.debug('Check forward: ignoring message as it is not from Telegram')
            return False

        if message.forward_from_chat is None:
            logger.debug('Check forward: ignoring message as it is not forwarded')
            return False

        enabled_channel_ids = self.enabled_chats.enabled_channel_ids()
        from_channel_id = message.forward_from_chat.id
        if from_channel_id not in enabled_channel_ids:
            logger.debug('Check forward: ignoring message as it is not from enabled channel')
            return False

        from_message_id = message.forward_from_message_id
        thread_message_id = message.message_id

        channel_state = self.space_state.ensure_channel_state(str(from_channel_id))
        reply_markup_str = channel_state.markup_queue.try_get(str(from_message_id))
        if reply_markup_str is None:
            reply_markup_str = channel_state.markup_trail.try_get(str(from_message_id))
        if reply_markup_str is None:
            logger.error(f'Was not able to get cached reply markup for {from_channel_id}')
            return True

        group_id = message.chat.id
        short_group_id = telegram_utils.get_short_chat_id(group_id)
        comments_url = f'https://t.me/c/{short_group_id}/999999999?thread={thread_message_id}'
        reply_markup = InlineKeyboardMarkup.de_json(reply_markup_str)
        reply_markup = markup_utils.add_url_button_to_markup(reply_markup=reply_markup,
                                                             text='💬',
                                                             url=comments_url)
        self.markup_synchronizer.add(channel_id=from_channel_id,
                                     message_id=from_message_id,
                                     reply_markup=reply_markup,
                                     to_top=True)
        return True
