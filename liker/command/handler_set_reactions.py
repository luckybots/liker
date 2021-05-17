import inject
import logging
from tengi.command.command_handler import *
from tengi import telegram_bot_utils

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

    def handle(self, context: CommandContext):
        if context.command == '/set_reactions':
            channel_id = context.get_mandatory_arg('channel_id')
            reactions = context.get_mandatory_arg('reactions')

            if not telegram_bot_utils.is_proper_chat_id(channel_id):
                context.reply('channel_id should be a number or start from @',
                              log_level=logging.INFO)
                return

            set_successfully = self.enabling_manager.try_set_reactions(channel_id=channel_id,
                                                                       reactions=reactions,
                                                                       reply_context=context)
            if not set_successfully:
                return

            context.reply(f'for {channel_id} reactions are {reactions}',
                          log_level=logging.INFO)
        else:
            raise ValueError(f'Unhandled command: {context.command}')
