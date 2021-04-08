import inject
import logging
from tengine.command.command_handler import *
from tengine import TelegramBot
from tengine import Config
from telebot.types import InlineKeyboardMarkup

from liker.state.enabled_channels import EnabledChannels
from liker.state.space_state import SpaceState
from liker.custom_markup import markup_utils
from liker.setup import constants

logger = logging.getLogger(__file__)


class CommandHandlerUpdateMarkup(CommandHandler):
    telegram_bot = inject.attr(TelegramBot)
    enabled_channels = inject.attr(EnabledChannels)
    space_state = inject.attr(SpaceState)

    def get_cards(self) -> Iterable[CommandCard]:
        return [CommandCard(command_str='/update_markup',
                            description='Set buttons according to reactions enabled',
                            is_admin=False),
                ]

    def handle(self,
               config: Config,
               chat_id,
               message: Message,
               args: Namespace,
               telegram_bot: TelegramBot,
               command_parser: CommandParser):
        if args.command == '/update_markup':
            ref_message: Message = message.reply_to_message
            if (ref_message is None) or (ref_message.forward_from_chat is None):
                telegram_bot.send_text(chat_id=chat_id,
                                       text='Send /update_markup in comments to target channel post')
                return

            channel_id = ref_message.forward_from_chat.id
            if not self.enabled_channels.is_enabled(str(channel_id)):
                telegram_bot.send_text(chat_id=chat_id,
                                       text='Liker is not enabled for the given channel')
                return

            channel_message_id = ref_message.forward_from_message_id
            str_trail_markup = self.space_state \
                .ensure_channel_state(str(channel_id)) \
                .markup_trail \
                .try_get(str(channel_message_id))
            trail_markup = None if (str_trail_markup is None) else InlineKeyboardMarkup.de_json(str_trail_markup)
            channel_dict = self.enabled_channels.get_channel_dict(str(channel_id))
            enabled_reactions = channel_dict['reactions']
            reply_markup = markup_utils.extend_reply_markup(current_markup=trail_markup,
                                                            enabled_reactions=enabled_reactions,
                                                            handler=constants.CHANNEL_POST_HANDLER,
                                                            case_id='')
            self.telegram_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                            message_id=channel_message_id,
                                                            reply_markup=reply_markup)
        else:
            raise ValueError(f'Unhandled command: {args.command}')

