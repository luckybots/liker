from unittest.mock import patch
import pytest
from pathlib import Path
from telebot import TeleBot
from tengi.app import App
from tengi.tests.test_utils import get_telegram_message_update


@pytest.fixture()
def project_data_path():
    return Path(__file__).parent.parent/'data'


def mock_get_updates(self, offset=None, limit=None, timeout=20, allowed_updates=None, long_polling_timeout = 20):
    if offset is None:  # on the first look_back call
        return []
    else:
        ping_u = get_telegram_message_update()
        ping_u.message.text = '/ping'
        return [ping_u]


def test_integrated_ping(tmp_path, project_data_path, caplog):
    import logging
    caplog.set_level(logging.DEBUG)

    with patch('liker.setup.constants.APP_DIR', tmp_path), \
         patch('liker.setup.constants.config_path', return_value=project_data_path / 'config_example.json'), \
         patch('liker.setup.constants.config_example_path', return_value=project_data_path / 'config_example.json'), \
         patch.object(App, 'should_interrupt', return_value=True), \
         patch.object(TeleBot, 'get_updates', new=mock_get_updates), \
         patch.object(TeleBot, 'send_message') as send_message:

        from liker.run import main

        main()

        send_message.assert_called_once()
        assert ('pong' in send_message.call_args.args) or \
               ('pong' in send_message.call_args.kwargs.values())
