from typing import Optional
import logging
import inject
from telebot.apihelper import ApiTelegramException
from tengine import Config, telegram_bot_utils, TelegramBot

from liker.state.enabled_channels import EnabledChannels

logger = logging.getLogger(__file__)


class EnablingManager:
    config = inject.attr(Config)
    telegram_bot = inject.attr(TelegramBot)
    enabled_channels = inject.attr(EnabledChannels)

    def try_set_reactions(self,
                          channel_id,
                          reactions: list,
                          reply_to_chat_id: Optional[int]) -> bool:
        enable_only_for = self.config['enable_only_for']
        if enable_only_for and (telegram_bot_utils.to_int_chat_id_if_possible(channel_id) not in enable_only_for):
            self._try_reply(chat_id=reply_to_chat_id,
                            text=f'Cannot enable for channel {channel_id}')
            return False

        try:
            channel_info = self.telegram_bot.bot.get_chat(channel_id)
        except ApiTelegramException:
            logging.info('Cannot get channel info, bot is not an admin in there')
            self._try_reply(chat_id=reply_to_chat_id,
                            text=f'Add bot as an administrator to {channel_id}')
            return False

        channel_id_int = channel_info.id

        linked_chat_id = channel_info.linked_chat_id
        if linked_chat_id is not None:
            try:
                linked_chat_admins = self.telegram_bot.bot.get_chat_administrators(linked_chat_id)
                if not linked_chat_admins:
                    raise ValueError('Got empty list of administrators')
            except (ApiTelegramException, ValueError) as ex:
                logging.info(f'Bot is not an admin in linked chat: {ex}')
                self._try_reply(chat_id=reply_to_chat_id,
                                text=f'Add bot as an administrator to the channel discussion group')
                return False

        self.enabled_channels.update_channel_dict(str_channel_id=str(channel_id_int),
                                                  reactions=reactions,
                                                  linked_chat_id=linked_chat_id)
        return True

    def _try_reply(self,
                   chat_id: Optional[int],
                   text: str):
        if chat_id is not None:
            self.telegram_bot.send_text(chat_id=chat_id, text=text)
