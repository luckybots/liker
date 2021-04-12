import inject
import logging
import time
from telebot.apihelper import ApiTelegramException
from tengine.command.command_handler import *
from tengine import TelegramBot, TelegramApi, telegram_api_utils, Config, telegram_error

from liker.setup import constants

logger = logging.getLogger(__file__)


class CommandHandlerTakeMessage(CommandHandler):
    telegram_bot = inject.attr(TelegramBot)
    telegram_api = inject.attr(TelegramApi)
    config = inject.attr(Config)

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

            from_message_id = args.message_id
            if from_message_id is None:
                self.telegram_bot.send_text(chat_id=chat_id,
                                            text='--message_id required')
                return

            n_backward_messages = args.n

            if n_backward_messages is None:
                n_backward_messages = 1

            arr_messages = self.telegram_api.get_chat_messages_backward(chat_id=channel_id,
                                                                        message_id=from_message_id,
                                                                        n_messages=n_backward_messages)
            n_messages = len(arr_messages)
            period = 60 / self.config['channel_rate_per_minute']
            response_text = f'There are {n_messages:,} messages, will take approximately {n_messages * period:,.0f} ' \
                            f'seconds. Bot will not to respond to other commands and buttons clicks till finish'
            self.telegram_bot.send_text(chat_id=chat_id,
                                        text=response_text)
            n_processed = 0
            for msg in arr_messages:
                try:
                    try:
                        # Verbose
                        if True:
                            if (n_processed > 0) and (n_processed % constants.TAKE_MESSAGE_VERBOSE_N == 0):
                                self.telegram_bot.send_text(chat_id=chat_id,
                                                            text=f'Processed {n_processed:,} messages')
                            n_processed += 1

                        new_reply_markup = telegram_api_utils.api_to_bot_markup(msg.reply_markup)
                        prev_bot = TelegramBot(token=prev_bot_token)
                        # Reset reply markup, needed for another bot to be able to modify it
                        prev_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                               message_id=msg.id,
                                                               reply_markup=None)
                        # Modify reply markup by the new bot
                        self.telegram_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                                        message_id=msg.id,
                                                                        reply_markup=new_reply_markup)
                        logger.info(f'Took {channel_id} message {msg.id}, will sleep for {period:.1f} seconds')
                        time.sleep(period)
                    except ApiTelegramException as ex:
                        logger.exception(ex)
                        if ex.error_code == telegram_error.TOO_MANY_REQUESTS:
                            time.sleep(10)
                        else:
                            raise ex
                except Exception as ex:
                    try:
                        self.telegram_bot.send_text(chat_id=chat_id,
                                                    text=f'Error processing message {msg.id}: {str(ex)}')
                    except ApiTelegramException as ex:
                        logger.exception(ex)
                        if ex.error_code == telegram_error.TOO_MANY_REQUESTS:
                            time.sleep(10)
                        else:
                            raise ex

            logger.info(f'take_messages done {channel_id}')
            self.telegram_bot.send_text(chat_id=chat_id,
                                        text=f'for {channel_id} message(s) were taken')
        else:
            raise ValueError(f'Unhandled command: {args.command}')
