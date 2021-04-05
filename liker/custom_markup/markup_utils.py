import logging
from telebot import types
from typing import Optional, Iterable
from tengine import telegram_utils

logger = logging.getLogger(__file__)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


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


def build_reply_markup(enabled_reactions: list,
                       state_dict: Optional[dict],
                       handler: str,
                       case_id: str) -> types.InlineKeyboardMarkup:
    state_reactions = {}
    if (state_dict is not None) and ('reactions' in state_dict):
        state_reactions = state_dict['reactions']
    buttons_obj = []
    for r in enabled_reactions:
        if r in state_reactions:
            counter = state_reactions[r]
            text = f'{r}{counter}'
        else:
            text = f'{r}'
        data = telegram_utils.encode_button_data(handler=handler,
                                                 case_id=case_id,
                                                 response=r)
        b = types.InlineKeyboardButton(text=text,
                                       callback_data=data)
        buttons_obj.append(b)

    return markup_from_buttons(buttons_obj)


def change_reaction_counter(reply_markup: types.InlineKeyboardMarkup, reaction: str, delta: int):
    for btn in iterate_markup_buttons(reply_markup):
        if reaction in btn.text:
            num_str = btn.text.replace(reaction, '').strip()

            num = _num_str_to_number(num_str)
            if num is None:
                logger.error(f'Cannot parse button reaction state: {btn.text}')
                continue
            num += delta
            num_str = '' if (num == 0) else f'{num}'

            t_new = f'{reaction}{num_str}'
            btn.text = t_new
            return
    raise Exception(f'Can not change reaction counter: {reply_markup.to_json()}')


def iterate_markup_buttons(reply_markup: types.InlineKeyboardMarkup) -> Iterable[types.InlineKeyboardButton]:
    for row in reply_markup.keyboard:
        for btn in row:
            yield btn


def markup_from_buttons(buttons: Iterable[types.InlineKeyboardButton]) -> types.InlineKeyboardMarkup:
    buttons = list(buttons)
    if len(buttons) == 4:
        rows = chunks(buttons, 2)
    else:
        rows = chunks(buttons, 3)
    reply_markup = types.InlineKeyboardMarkup()
    for r in rows:
        reply_markup.add(*r)
    return reply_markup


def add_url_button_to_markup(reply_markup: types.InlineKeyboardMarkup,
                             text: str,
                             url: str):
    new_b = types.InlineKeyboardButton(text, url)
    new_buttons = list(iterate_markup_buttons(reply_markup)) + [new_b]
    return markup_from_buttons(new_buttons)


def markup_has_button(reply_markup: types.InlineKeyboardMarkup, text: str):
    result = False
    for btn in iterate_markup_buttons(reply_markup):
        result = text in btn.text
        if result:
            break
    return result

