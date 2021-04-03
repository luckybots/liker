import logging
from typing import Optional
import inject
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from tengine import Config, telegram_utils
from tengine.preserve.preserver import *

logger = logging.getLogger(__file__)


class ChannelState(Preserver):
    config = inject.attr(Config)

    def __init__(self, state_file_path: Path):
        super().__init__(state_file_path)

        last_reactions_path = state_file_path.with_name(state_file_path.stem +
                                                        '_last_reactions' +
                                                        state_file_path.suffix)
        self.last_reactions = Preserver(last_reactions_path)

    @staticmethod
    def change_reaction_counter(reply_markup: InlineKeyboardMarkup, reaction: str, delta: int):
        for row in reply_markup.keyboard:
            btn: InlineKeyboardButton
            for btn in row:
                _handler, _case_id, button_response = telegram_utils.decode_button_data(btn.callback_data)

                if reaction == button_response:
                    num_str = btn.text.replace(reaction, '').strip()

                    num = ChannelState._num_str_to_number(num_str)
                    if num is None:
                        logger.error(f'Cannot parse button reaction state: {btn.text}')
                        continue
                    num += delta
                    num_str = '' if (num == 0) else f'{num}'

                    t_new = f'{reaction}{num_str}'
                    btn.text = t_new
                    return
        raise Exception(f'Can not change reaction counter: {reply_markup.to_json()}')

    @staticmethod
    def _num_str_to_number(num_str):
        result = None
        if num_str == '':
            result = 0
        else:
            try:
                result = int(num_str)
            except ValueError:
                pass
        return result

    def ensure_markup_queue(self):
        if 'markup_queue' not in self.state:
            self.state['markup_queue'] = {}
        return self.state['markup_queue']

    def update_markup_queue(self, markup_queue):
        self.state['markup_queue'] = markup_queue

    def has_reaction_hash(self, reaction_hash: str) -> bool:
        if 'hashes' not in self.last_reactions.state:
            return False

        last_reaction_hashes = self.last_reactions.state['hashes']
        return reaction_hash in last_reaction_hashes

    def save_last_reaction_hashes(self, last_reaction_hashes):
        n_to_keep = self.config['last_reactions']
        last_reaction_hashes = last_reaction_hashes[:n_to_keep]
        self.last_reactions.state['hashes'] = last_reaction_hashes

    def add_reaction_hash(self, reaction_hash: str):
        if 'hashes' not in self.last_reactions.state:
            self.last_reactions.state['hashes'] = []
        last_reaction_hashes = self.last_reactions.state['hashes']
        last_reaction_hashes.insert(0, reaction_hash)
        self.save_last_reaction_hashes(last_reaction_hashes)

    def remove_reaction_hash(self, reaction_hash: str):
        if 'hashes' not in self.last_reactions.state:
            return
        last_reaction_hashes = self.last_reactions.state['hashes']
        last_reaction_hashes = [x for x in last_reaction_hashes if x != reaction_hash]
        self.save_last_reaction_hashes(last_reaction_hashes)
