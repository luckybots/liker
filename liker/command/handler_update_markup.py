import inject
import logging
from tengine.command.command_handler import *
from telebot.types import InlineKeyboardMarkup, Message
from typing import Tuple
from tengine import CommandMissingArgError

from liker.state.enabled_channels import EnabledChannels
from liker.state.space_state import SpaceState
from liker.custom_markup import markup_utils
from liker.setup import constants

logger = logging.getLogger(__file__)


class CommandHandlerUpdateMarkup(CommandHandler):
    enabled_channels = inject.attr(EnabledChannels)
    space_state = inject.attr(SpaceState)

    def get_cards(self) -> Iterable[CommandCard]:
        return [CommandCard(command_str='/update_markup',
                            description='Set buttons according to reactions enabled',
                            is_admin=True),
                CommandCard(command_str='/force_counter',
                            description='Set custom value for the reactions counter',
                            is_admin=True),
                ]

    def handle(self, context: CommandContext):
        if context.command == '/update_markup':
            channel_id, channel_message_id = self._get_root_message_info(context)
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
            context.telegram_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                               message_id=channel_message_id,
                                                               reply_markup=reply_markup)
            context.reply('Done', log_level=logging.INFO)

        elif context.command == '/force_counter':
            var_name = context.get_mandatory_arg('name')
            var_value_int = context.get_mandatory_arg('value', cast_func=int)

            channel_id, channel_message_id = self._get_root_message_info(context)

            markup_trail = self.space_state.ensure_channel_state(str(channel_id)).markup_trail
            reply_markup_str = markup_trail.try_get(str(channel_message_id))
            if reply_markup_str is None:
                context.reply('Markup is not cached, press a reaction button first')
                return

            reply_markup = InlineKeyboardMarkup.de_json(reply_markup_str)
            markup_utils.change_reaction_counter(reply_markup, reaction=var_name, value=var_value_int, is_delta=False)
            context.telegram_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                               message_id=channel_message_id,
                                                               reply_markup=reply_markup)
            context.reply('Done', log_level=logging.INFO)
        else:
            raise ValueError(f'Unhandled command: {context.command}')

    def _get_root_message_info(self, context: CommandContext) -> Tuple[int, int]:
        ref_message: Message = context.sender_message.reply_to_message
        if (ref_message is None) or (ref_message.forward_from_chat is None):
            context.reply(f'Send {context.command} in comments to target channel post')
            raise CommandMissingArgError(f'Command {context.command} sent not as a reply to channel post')

        channel_id = ref_message.forward_from_chat.id
        if not self.enabled_channels.is_enabled(str(channel_id)):
            context.reply('Liker is not enabled for the given channel')
            raise CommandMissingArgError(f'Command {context.command} sent for not enabled channel')

        channel_message_id = ref_message.forward_from_message_id
        return channel_id, channel_message_id
