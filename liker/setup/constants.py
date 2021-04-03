from pathlib import Path
import sys

LOG_FORMAT = '%(module)-12s: %(asctime)s %(levelname)s %(message)s'

APP_DIR = Path(sys.modules['__main__'].__file__).parent.parent

UPDATE_SECONDS = 1
RESTART_SECONDS = 10

BOT_LOOK_BACK_DAYS = 1
LONG_POLLING_TIMEOUT = 1

MESSAGES_LOG_PREFIX = 'messages'

BUTTON_HANDLER = 'lik'

REACTION_HASH_BYTES = 4

ABUSE_PERIOD_SECONDS = 600
ABUSE_THRESHOLD = 1000
ABUSE_JANITOR_SECONDS = 1 * 60 * 60


def data_dir():
    return APP_DIR/'data'


def state_dir():
    return data_dir()/'state'


def config_path():
    return data_dir()/'config.json'


def config_example_path():
    return data_dir()/'config_example.json'


def log_dir():
    return data_dir()/'logs'


def csv_log_dir():
    return data_dir()/'csv_logs'


def messages_log_dir():
    return csv_log_dir()/'messages'


def chat_ids_state_path():
    return state_dir()/'chat_ids.json'


def enabled_channels_state_path():
    return state_dir()/'enabled_channels.json'


def space_dir():
    return state_dir()/'space'
