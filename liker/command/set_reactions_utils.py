from typing import Optional
import logging
from telebot.apihelper import ApiTelegramException
from tengine import Config, telegram_utils, TelegramBot

from liker.state.enabled_channels import EnabledChannels

logging = logging.getLogger(__file__)


def try_set_reactions(config: Config,
                      telegram_bot: TelegramBot,
                      enabled_channels: EnabledChannels,
                      channel_id,
                      reactions: list,
                      reply_to_chat_id: Optional[int]) -> bool:
    enable_only_for = config['enable_only_for']
    if enable_only_for and (telegram_utils.to_int_chat_id_if_possible(channel_id) not in enable_only_for):
        _try_reply(telegram_bot=telegram_bot,
                   chat_id=reply_to_chat_id,
                   text=f'Cannot enable for channel {channel_id}')
        return False

    try:
        channel_info = telegram_bot.bot.get_chat(channel_id)
    except ApiTelegramException:
        logging.info('Cannot get channel info, bot is not an admin in there')
        _try_reply(telegram_bot=telegram_bot,
                   chat_id=reply_to_chat_id,
                   text=f'Add bot as an administrator to {channel_id}')
        return False

    channel_id_int = channel_info.id

    linked_chat_id = channel_info.linked_chat_id
    if linked_chat_id is not None:
        try:
            linked_chat_admins = telegram_bot.bot.get_chat_administrators(linked_chat_id)
            if not linked_chat_admins:
                raise ValueError('Got empty list of administrators')
        except (ApiTelegramException, ValueError) as ex:
            logging.info(f'Bot is not an admin in linked chat: {ex}')
            _try_reply(telegram_bot=telegram_bot,
                       chat_id=reply_to_chat_id,
                       text=f'Add bot as an administrator to the channel discussion group')
            return False

    enabled_channels.update_channel_dict(str_channel_id=str(channel_id_int),
                                         reactions=reactions,
                                         linked_chat_id=linked_chat_id)
    return True


def _try_reply(telegram_bot: TelegramBot,
               chat_id: Optional[int],
               text: str):
    if chat_id is not None:
        telegram_bot.send_text(chat_id=chat_id, text=text)
