import logging
import inject
from telebot.types import InlineKeyboardMarkup
from tengine import telegram_bot_utils
from tengine.telegram.inbox_handler import *
from tengine.telegram.constants import TELEGRAM_USER_ID

from liker.state.enabled_channels import EnabledChannels
from liker.state.space_state import SpaceState
from liker.custom_markup import markup_utils
from liker.custom_markup.markup_synchronizer import MarkupSynchronizer
from liker.setup import constants

logger = logging.getLogger(__file__)


class CommentHandler(TelegramInboxHandler):
    """
    Handles channel post comments in the linked group. Updates the counter of the comments.
    Unfortunately the bot can't receive events of message deletion -- thus the counter doesn't decrease in case of
    comments were deleted.
    """
    enabled_chats = inject.attr(EnabledChannels)
    space_state = inject.attr(SpaceState)
    markup_synchronizer = inject.attr(MarkupSynchronizer)

    def message(self, message: types.Message) -> bool:
        if not telegram_bot_utils.is_group_message(message):
            return False

        if self._check_forward_from_channel(message):
            return True

        if self._check_reply_to_channel_post(message):
            return True

        return False

    def _check_forward_from_channel(self, message: types.Message) -> bool:
        if message.from_user.id != TELEGRAM_USER_ID:
            logger.debug('Check forward: ignoring message as it is not from Telegram')
            return False

        if message.forward_from_chat is None:
            logger.debug('Check forward: ignoring message as it is not forwarded')
            return False

        enabled_channel_ids = self.enabled_chats.enabled_channel_ids()
        channel_id = message.forward_from_chat.id
        if channel_id not in enabled_channel_ids:
            logger.debug('Check forward: ignoring message as it is not from enabled channel')
            return False

        channel_message_id = message.forward_from_message_id
        thread_message_id = message.message_id

        reply_markup = self._try_find_reply_markup(channel_id=channel_id, message_id=channel_message_id)
        if reply_markup is None:
            logger.error(f'Was not able to get cached reply markup for {channel_id}')
            return True

        group_id = message.chat.id
        reply_markup = self._ensure_comment_button(reply_markup=reply_markup,
                                                   group_id=group_id,
                                                   thread_message_id=thread_message_id)
        self.markup_synchronizer.add(channel_id=channel_id,
                                     message_id=channel_message_id,
                                     reply_markup=reply_markup,
                                     to_top=True)
        return True

    def _check_reply_to_channel_post(self, message: types.Message) -> bool:
        ref_message: types.Message = message.reply_to_message
        if ref_message is None:
            return False

        group_id = message.chat.id
        if ref_message.forward_from_chat is not None:
            channel_id = ref_message.forward_from_chat.id
            channel_message_id = ref_message.forward_from_message_id
            thread_message_id = ref_message.message_id
        else:
            channel_id = self.enabled_chats.try_get_channel_id_for_linked_chat_id(group_id)
            if channel_id is None:
                return False
            channel_state = self.space_state.ensure_channel_state(str(channel_id))
            ref_message_trail = channel_state.comment_trail.try_get(str_message_id=str(ref_message.message_id))
            if ref_message_trail is None:
                return False
            channel_message_id = ref_message_trail['channel_message_id']
            thread_message_id = ref_message_trail['thread_message_id']

        enabled_channel_ids = self.enabled_chats.enabled_channel_ids()
        if channel_id not in enabled_channel_ids:
            return False

        reply_markup = self._try_find_reply_markup(channel_id=channel_id, message_id=channel_message_id)
        if reply_markup is None:
            logger.warning(f'Ignoring a reply message as there is not cached reply markup: channel {channel_id}, '
                           f'channel message {channel_message_id}')
            return True

        reply_markup = self._ensure_comment_button(reply_markup=reply_markup,
                                                   group_id=group_id,
                                                   thread_message_id=thread_message_id)
        markup_utils.change_reaction_counter(reply_markup,
                                             reaction=constants.COMMENT_TEXT,
                                             value=1,
                                             is_delta=True)
        self.markup_synchronizer.add(channel_id=channel_id,
                                     message_id=channel_message_id,
                                     reply_markup=reply_markup,
                                     to_top=True)

        comment_message_id = message.message_id
        comment_dict = {
            'channel_message_id': channel_message_id,
            'thread_message_id': thread_message_id,
        }
        channel_state = self.space_state.ensure_channel_state(str(channel_id))
        channel_state.comment_trail.add(str_message_id=str(comment_message_id),
                                        comment_dict=comment_dict)
        return True

    @staticmethod
    def _ensure_comment_button(reply_markup: InlineKeyboardMarkup,
                               group_id: int,
                               thread_message_id: int) -> InlineKeyboardMarkup:
        if not markup_utils.markup_has_button(reply_markup, constants.COMMENT_TEXT):
            short_group_id = telegram_bot_utils.get_short_chat_id(group_id)
            comments_url = f'https://t.me/c/{short_group_id}/999999999?thread={thread_message_id}'
            reply_markup = markup_utils.add_url_button_to_markup(reply_markup=reply_markup,
                                                                 text=constants.COMMENT_TEXT,
                                                                 url=comments_url)
        return reply_markup

    def _try_find_reply_markup(self, channel_id, message_id):
        channel_state = self.space_state.ensure_channel_state(str(channel_id))
        reply_markup_str = channel_state.markup_queue.try_get(str(message_id))
        if reply_markup_str is None:
            reply_markup_str = channel_state.markup_trail.try_get(str(message_id))
        result = None if (reply_markup_str is None) else InlineKeyboardMarkup.de_json(reply_markup_str)
        return result
