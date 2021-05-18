import inject
import logging
import time
from telebot.apihelper import ApiTelegramException
from tengi.command.command_handler import *
from tengi import TelegramBot, TelegramApi, telegram_api_utils, telegram_error

from liker.setup import constants
from liker.custom_markup import markup_utils

logger = logging.getLogger(__file__)


class CommandHandlerTakeMessage(CommandHandler):
    def __init__(self, use_telegram_user_api: bool):
        self.use_telegram_user_api = use_telegram_user_api

        self.telegram_api = None
        if self.use_telegram_user_api:
            self.telegram_api = inject.instance(TelegramApi)

    def get_cards(self) -> Iterable[CommandCard]:
        return [CommandCard(command_str='/take_messages',
                            description='Take ownership over channel message(s)',
                            is_admin=True),
                ]

    def handle(self, context: CommandContext):
        if context.command == '/take_messages':
            if not self.use_telegram_user_api:
                context.reply('This command requires use_telegram_user_api to be enabled in config')
                return

            channel_id = context.get_mandatory_arg('channel_id')
            prev_bot_token = context.get_mandatory_arg('bot_token')
            from_message_id = context.get_mandatory_arg('message_id')
            n_backward_messages = context.get_optional_arg('n', default=1)

            try:
                arr_messages = self.telegram_api.get_chat_messages_backward(chat_id=channel_id,
                                                                            message_id=from_message_id,
                                                                            n_messages=n_backward_messages)
            except ValueError as ex:
                # Error like "Could not find the input entity for PeerChannel(channel_id=1322520409)", most likely
                # means the user wasn't added to the channel or channel doesn't exist
                context.reply(text=str(ex), log_level=logging.INFO)
                return

            n_messages = len(arr_messages)
            period = 60 / context.config['channel_rate_per_minute']
            response_text = f'There are {n_messages:,} messages, will take approximately {n_messages * period:,.0f} ' \
                            f'seconds. Bot will not to respond to other commands and buttons clicks till finish'
            context.reply(response_text, log_level=logging.INFO)
            n_processed = 0
            for msg in arr_messages:
                try:
                    try:
                        iteration_begin = time.time()
                        # Verbose
                        if True:
                            if (n_processed > 0) and (n_processed % constants.TAKE_MESSAGE_VERBOSE_N == 0):
                                context.reply(f'Processed {n_processed:,} messages', log_level=logging.INFO)
                            n_processed += 1

                        new_reply_markup = telegram_api_utils.api_to_bot_markup(msg.reply_markup)
                        markup_utils.assign_reaction_buttons_data(markup=new_reply_markup,
                                                                  handler=constants.CHANNEL_POST_HANDLER,
                                                                  case_id='')
                        prev_bot = TelegramBot(token=prev_bot_token)
                        # Reset reply markup, needed for another bot to be able to modify it
                        prev_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                               message_id=msg.id,
                                                               reply_markup=None)
                        # Modify reply markup by the new bot
                        context.telegram_bot.bot.edit_message_reply_markup(chat_id=channel_id,
                                                                           message_id=msg.id,
                                                                           reply_markup=new_reply_markup)
                        logger.debug(f'Took {channel_id} message {msg.id}, will sleep for {period:.1f} seconds')

                        iteration_end = time.time()
                        iteration_remaining = period - (iteration_end - iteration_begin)
                        if iteration_remaining > 0:
                            logger.debug(f'Sleeping {iteration_remaining:.2f}')
                            time.sleep(iteration_remaining)
                    except ApiTelegramException as ex:
                        if ex.error_code == telegram_error.TOO_MANY_REQUESTS:
                            logging.warning(ex)
                            time.sleep(10)
                        elif ex.error_code == telegram_error.UNAUTHORIZED:
                            logging.info(str(ex))
                            context.reply('Bot has no rights to perform the operation')
                            return
                        elif ex.error_code == telegram_error.BAD_REQUEST:
                            logging.info(str(ex))
                            context.reply(f'Message {msg.id} was deleted or not yet posted')
                        else:
                            raise ex
                except Exception as ex:
                    logger.exception(ex)
                    context.reply(f'Error processing message {msg.id}: {str(ex)}')

            context.reply(f'for {channel_id} {n_messages} message(s) were taken',
                          log_level=logging.INFO)
        else:
            raise ValueError(f'Unhandled command: {context.command}')
