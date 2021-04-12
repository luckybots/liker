import inject
import logging
from tengine.command.command_handler import *
from tengine import telegram_bot_utils

from liker.state.enabled_channels import EnabledChannels
from liker.enabling_manager import EnablingManager

logger = logging.getLogger(__file__)


class CommandHandlerSetReactions(CommandHandler):
    enabled_channels = inject.attr(EnabledChannels)
    enabling_manager = inject.attr(EnablingManager)

    def get_cards(self) -> Iterable[CommandCard]:
        return [CommandCard(command_str='/set_reactions',
                            description='Set reactions for the given channel',
                            is_admin=False),
                ]

    def handle(self,
               sender_chat_id,
               sender_message: Message,
               args: Namespace):
        if args.command == '/set_reactions':
            channel_id = args.channel_id
            if channel_id is None:
                self.telegram_bot.send_text(chat_id=sender_chat_id,
                                            text='--channel_id required')
                return

            reactions = args.reactions
            if (reactions is None) or (len(reactions) == 0):
                self.telegram_bot.send_text(chat_id=sender_chat_id,
                                            text='--reactions required')
                return

            if not telegram_bot_utils.is_proper_chat_id(channel_id):
                self.telegram_bot.send_text(chat_id=sender_chat_id,
                                            text='channel_id should be a number or start from @')
                return

            set_successfully = self.enabling_manager.try_set_reactions(channel_id=channel_id,
                                                                       reactions=reactions,
                                                                       reply_to_chat_id=sender_chat_id)
            if not set_successfully:
                return

            logger.info(f'set_reactions {channel_id}, {reactions}')
            self.telegram_bot.send_text(chat_id=sender_chat_id,
                                        text=f'for {channel_id} reactions are {reactions}')
        else:
            raise ValueError(f'Unhandled command: {args.command}')

