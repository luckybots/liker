import inject
import logging
from tengine.command.command_handler import *
from tengine import TelegramBot

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

            self.enabled_channels.update_channel_dict(str_channel_id=str(channel_id),
                                                      reactions=reactions)
            logger.info(f'set_reactions {channel_id}, {reactions}')
            self.telegram_bot.send_text(chat_id=chat_id,
                                        text=f'for {channel_id} reactions are {reactions}')
        else:
            raise ValueError(f'Unhandled command: {args.command}')
