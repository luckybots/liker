import inject
import logging
from tengine.command.command_handler import *
from tengine import TelegramBot, TelegramApi, telegram_api_utils

logger = logging.getLogger(__file__)


class CommandHandlerTakeMessage(CommandHandler):
    telegram_bot = inject.attr(TelegramBot)
    telegram_api = inject.attr(TelegramApi)

    def get_cards(self) -> Iterable[CommandCard]:
        return [CommandCard(command_str='/take_messages',
                            description='Take ownership over channel message(s)',
                            is_admin=True),
                ]

    def handle(self,
               config: Config,
               chat_id,
               message: Message,
               args: Namespace,
               telegram_bot: TelegramBot,
               command_parser: CommandParser):
        if args.command == '/take_messages':
            channel_id = args.channel_id
            if channel_id is None:
                self.telegram_bot.send_text(chat_id=chat_id,
                                            text='--channel_id required')
                return

            prev_bot_token = args.bot_token
            if prev_bot_token is None:
                self.telegram_bot.send_text(chat_id=chat_id,
                                            text='--bot_id required')
                return

            message_id = args.message_id

            if message_id is not None:
                msg = self.telegram_api.get_chat_message(chat_id=channel_id,
                                                         message_id=message_id)
                new_reply_markup = telegram_api_utils.api_to_bot_markup(msg.reply_markup)
                prev_bot = TelegramBot(token=prev_bot_token)
                # Reset reply markup, needed for another bot to be able to modify it
                prev_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                       message_id=message_id,
                                                       reply_markup=None)
                # Modify reply markup by the new bot
                self.telegram_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                                message_id=message_id,
                                                                reply_markup=new_reply_markup)
            else:
                raise Exception(f'Not yet implemented')

            logger.info(f'take_messages done {channel_id}, {message_id}')
            self.telegram_bot.send_text(chat_id=chat_id,
                                        text=f'for {channel_id} message(s) were taken')
        else:
            raise ValueError(f'Unhandled command: {args.command}')
