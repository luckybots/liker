from inject import Binder
import inject
from tengi import *

from liker.setup import constants
from liker.command.params import command_params
from liker.state.enabled_channels import EnabledChannels
from liker.state.space_state import SpaceState
from liker.custom_markup.markup_synchronizer import MarkupSynchronizer
from liker.custom_markup.channel_post_handler import ChannelPostHandler
from liker.custom_markup.comment_handler import CommentHandler
from liker.command.handler_set_reactions import CommandHandlerSetReactions
from liker.enabling_manager import EnablingManager
from liker.command.handler_update_markup import CommandHandlerUpdateMarkup
from liker.command.handler_take_message import CommandHandlerTakeMessage


def bind_app_dependencies(binder: Binder):
    binder.bind_to_constructor(App, lambda: App(update_funcs=[inject.instance(TelegramInboxHub).update,
                                                              inject.instance(MarkupSynchronizer).update,
                                                              inject.instance(AbuseJanitor).update,
                                                              inject.instance(SpaceState).update],
                                                update_seconds=constants.UPDATE_SECONDS,
                                                restart_seconds=constants.RESTART_SECONDS))
    binder.bind(Config, Config(config_path=constants.config_path(),
                               example_path=constants.config_example_path()))

    binder.bind_to_constructor(Hasher, lambda: Hasher(config=inject.instance(Config)))
    binder.bind_to_constructor(TelegramBot, lambda: TelegramBot(token=inject.instance(Config)['bot_token']))
    binder.bind_to_constructor(TelegramApi,
                               lambda: TelegramApi(
                                   api_session_name=str(constants.data_dir()
                                                        / inject.instance(Config)['telegram_api_session']),
                                   api_id=inject.instance(Config)['telegram_api_id'],
                                   api_hash=inject.instance(Config)['telegram_api_hash']))
    binder.bind_to_constructor(TelegramCursor,
                               lambda: TelegramCursor(bot=inject.instance(TelegramBot),
                                                      look_back_days=constants.BOT_LOOK_BACK_DAYS,
                                                      long_polling_timeout=constants.LONG_POLLING_TIMEOUT))

    binder.bind_to_constructor(CommandHandlerPool, lambda: CommandHandlerPool(handlers=[
        CommandHandlerEssentials(),
        CommandHandlerPassword(),
        CommandHandlerConfig(),
        CommandHandlerSetReactions(),
        CommandHandlerUpdateMarkup(),
        CommandHandlerTakeMessage(use_telegram_user_api=inject.instance(Config)['use_telegram_user_api']),
    ]))
    binder.bind_to_constructor(CommandParser, lambda: CommandParser(handler_pool=inject.instance(CommandHandlerPool),
                                                                    params=command_params))
    binder.bind_to_constructor(CommandHub, lambda: CommandHub(config=inject.instance(Config),
                                                              telegram_bot=inject.instance(TelegramBot),
                                                              parser=inject.instance(CommandParser),
                                                              handler_pool=inject.instance(CommandHandlerPool)))
    binder.bind_to_constructor(MessagesLogger,
                               lambda: MessagesLogger(dir_path=constants.messages_log_dir(),
                                                      file_name_prefix=constants.MESSAGES_LOG_PREFIX,
                                                      command_parser=inject.instance(CommandHub).parser,
                                                      hasher=inject.instance(Hasher),
                                                      chat_types=constants.MESSAGES_LOG_CHAT_TYPES))
    binder.bind_to_constructor(TelegramInboxHub,
                               lambda: TelegramInboxHub(telegram_cursor=inject.instance(TelegramCursor),
                                                        chain_handlers=[inject.instance(CommandHub),
                                                                        inject.instance(ChannelPostHandler),
                                                                        inject.instance(CommentHandler)]))
    binder.bind_to_constructor(ChatIdPreserver,
                               lambda: ChatIdPreserver(state_file_path=constants.chat_ids_state_path()))
    binder.bind_to_constructor(EnabledChannels,
                               lambda: EnabledChannels(state_file_path=constants.enabled_channels_state_path()))
    binder.bind_to_constructor(SpaceState, lambda: SpaceState(constants.space_dir()))
    binder.bind_to_constructor(MarkupSynchronizer, lambda: MarkupSynchronizer())
    binder.bind_to_constructor(ChannelPostHandler, lambda: ChannelPostHandler())
    binder.bind_to_constructor(CommentHandler, lambda: CommentHandler())
    binder.bind_to_constructor(AbuseDetector, lambda: AbuseDetector(period_seconds=constants.ABUSE_PERIOD_SECONDS,
                                                                    abuse_threshold=constants.ABUSE_THRESHOLD))
    binder.bind_to_constructor(AbuseJanitor, lambda: AbuseJanitor(abuse_detector=inject.instance(AbuseDetector),
                                                                  period_seconds=constants.ABUSE_JANITOR_SECONDS))
    binder.bind_to_constructor(EnablingManager, lambda: EnablingManager())
