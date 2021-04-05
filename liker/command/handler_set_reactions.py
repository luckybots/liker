import inject
import logging
from telebot.apihelper import ApiTelegramException
from tengine.command.command_handler import *
from tengine import TelegramBot, telegram_utils

from liker.state.enabled_channels import EnabledChannels

logger = logging.getLogger(__file__)


class CommandHandlerSetReactions(CommandHandler):
    enabled_channels = inject.attr(EnabledChannels)
    telegram_bot = inject.attr(TelegramBot)

    def get_cards(self) -> Iterable[CommandCard]:
        return [CommandCard(command_str='/set_reactions',
                            description='Set reactions for the given channel',
                            is_admin=False),
                ]

    def handle(self,
               config: Config,
               chat_id,
               args: Namespace,
               telegram_bot: TelegramBot,
               command_parser: CommandParser):
        if args.command == '/set_reactions':
            channel_id = args.channel_id
            if channel_id is None:
                self.telegram_bot.send_text(chat_id=chat_id,
                                            text='--channel_id required')
                return

            reactions = args.reactions
            if (reactions is None) or (len(reactions) == 0):
                self.telegram_bot.send_text(chat_id=chat_id,
                                            text='--reactions required')
                return

            if not telegram_utils.is_proper_chat_id(channel_id):
                self.telegram_bot.send_text(chat_id=chat_id,
                                            text='channel_id should be a number or start from @')
                return

            try:
                channel_info = self.telegram_bot.bot.get_chat(channel_id)
            except ApiTelegramException:
                logging.info('Cannot get channel info, bot is not an admin in there')
                self.telegram_bot.send_text(chat_id=chat_id,
                                            text=f'Add bot as an administrator to {channel_id}')
                return

            channel_id_int = channel_info.id

            linked_chat_id = channel_info.linked_chat_id
            if linked_chat_id is not None:
                try:
                    linked_chat_admins = self.telegram_bot.bot.get_chat_administrators(linked_chat_id)
                    if not linked_chat_admins:
                        raise ValueError('Got empty list of administrators')
                except (ApiTelegramException, ValueError) as ex:
                    logging.info(f'Bot is not an admin in linked chat: {ex}')
                    self.telegram_bot.send_text(chat_id=chat_id,
                                                text=f'Add bot as an administrator to the channel discussion group')
                    return

            self.enabled_channels.update_channel_dict(str_channel_id=str(channel_id_int),
                                                      reactions=reactions,
                                                      linked_chat_id=linked_chat_id)
            logger.info(f'set_reactions {channel_id_int}, {reactions}, linked {linked_chat_id}')
            self.telegram_bot.send_text(chat_id=chat_id,
                                        text=f'for {channel_id} reactions are {reactions}')
        else:
            raise ValueError(f'Unhandled command: {args.command}')
