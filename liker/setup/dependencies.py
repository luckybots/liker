from inject import Binder
import inject
from tengine import *

from liker.setup import constants
from liker.command.params import command_params
from liker.state.enabled_channels import EnabledChannels
from liker.state.space_state import SpaceState
from liker.button.markup_sync_queue import MarkupSyncQueue
from liker.button.button_handler import ButtonHandler


def bind_app_dependencies(binder: Binder):
    binder.bind_to_constructor(App, lambda: App(update_funcs=[inject.instance(TelegramInboxHub).update,
                                                              inject.instance(MarkupSyncQueue).update,
                                                              inject.instance(AbuseJanitor).update],
                                                update_seconds=constants.UPDATE_SECONDS,
                                                restart_seconds=constants.RESTART_SECONDS))
    binder.bind(Config, Config(config_path=constants.config_path(),
                               example_path=constants.config_example_path()))
    binder.bind_to_constructor(Hasher, lambda: Hasher(config=inject.instance(Config)))
    binder.bind_to_constructor(TelegramBot, lambda: TelegramBot(token=inject.instance(Config)['bot_token']))
    binder.bind_to_constructor(TelegramCursor,
                               lambda: TelegramCursor(bot=inject.instance(TelegramBot),
                                                      look_back_days=inject.instance(Config)['bot_look_back_days']))
    binder.bind_to_constructor(CommandHub, lambda: CommandHub(config=inject.instance(Config),
                                                              handler_classes=[CommandHandlerEssentials,
                                                                               CommandHandlerPassword,
                                                                               CommandHandlerConfig],
                                                              params=command_params,
                                                              telegram_bot=inject.instance(TelegramBot)))
    binder.bind_to_constructor(MessagesLogger,
                               lambda: MessagesLogger(dir_path=constants.messages_log_dir(),
                                                      file_name_prefix=constants.MESSAGES_LOG_PREFIX,
                                                      command_parser=inject.instance(CommandHub).parser,
                                                      hasher=inject.instance(Hasher)))
    binder.bind_to_constructor(TelegramInboxHub,
                               lambda: TelegramInboxHub(telegram_cursor=inject.instance(TelegramCursor),
                                                        chain_handlers=[inject.instance(CommandHub),
                                                                        inject.instance(ButtonHandler)]))
    binder.bind_to_constructor(ChatIdPreserver,
                               lambda: ChatIdPreserver(state_file_path=constants.chat_ids_state_path()))
    binder.bind_to_constructor(EnabledChannels,
                               lambda: EnabledChannels(state_file_path=constants.enabled_channels_state_path()))
    binder.bind_to_constructor(SpaceState, lambda: SpaceState(constants.space_dir()))
    binder.bind_to_constructor(MarkupSyncQueue, lambda: MarkupSyncQueue())
    binder.bind_to_constructor(ButtonHandler, lambda: ButtonHandler())
    binder.bind_to_constructor(AbuseDetector, lambda: AbuseDetector(period_seconds=constants.ABUSE_PERIOD_SECONDS,
                                                                    abuse_threshold=constants.ABUSE_THRESHOLD))
    binder.bind_to_constructor(AbuseJanitor, lambda: AbuseJanitor(abuse_detector=inject.instance(AbuseDetector),
                                                                  period_seconds=constants.ABUSE_JANITOR_SECONDS))
