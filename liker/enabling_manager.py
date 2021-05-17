import logging
import inject
from typing import Optional
from telebot.apihelper import ApiTelegramException
from tengi import Config, telegram_bot_utils, TelegramBot, ReplyContext

from liker.state.enabled_channels import EnabledChannels

logger = logging.getLogger(__file__)


class EnablingManager:
    config = inject.attr(Config)
    telegram_bot = inject.attr(TelegramBot)
    enabled_channels = inject.attr(EnabledChannels)

    def try_set_reactions(self,
                          channel_id,
                          reactions: list,
                          reply_context: ReplyContext,
                          sender_id_to_check: Optional[int]) -> bool:
        enable_only_for = self.config['enable_only_for']
        if enable_only_for and (telegram_bot_utils.to_int_chat_id_if_possible(channel_id) not in enable_only_for):
            reply_context.reply(f'Cannot enable for channel {channel_id}')
            return False

        try:
            channel_info = self.telegram_bot.bot.get_chat(channel_id)

            # Check sender user is an admin in the target chat
            if sender_id_to_check is not None:
                channel_admins = self.telegram_bot.bot.get_chat_administrators(channel_id)
                sender_is_admin = any([a.user.id == sender_id_to_check for a in channel_admins])
                if not sender_is_admin:
                    reply_context.reply(
                        'Cannot set reactions for the given chat as the sender is not an admin in there',
                        log_level=logging.INFO)
                    return False
        except ApiTelegramException:
            logging.info('Cannot get channel info, bot is not an admin in there')
            reply_context.reply(f'Add bot as an administrator to {channel_id}')
            return False



        channel_id_int = channel_info.id

        linked_chat_id = channel_info.linked_chat_id
        self.enabled_channels.update_channel_dict(str_channel_id=str(channel_id_int),
                                                  reactions=reactions,
                                                  linked_chat_id=linked_chat_id)
        return True
