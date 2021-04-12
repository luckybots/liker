import logging
from telebot import types
from typing import Iterable, List, Optional
from tengine import telegram_bot_utils

from liker.setup import constants

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


def extend_reply_markup(current_markup: Optional[types.InlineKeyboardMarkup],
                        enabled_reactions: list,
                        handler: str,
                        case_id: str,
                        include_comment=True) -> types.InlineKeyboardMarkup:
    current_buttons: List[types.InlineKeyboardButton] = [] if (current_markup is None) \
        else list(iterate_markup_buttons(current_markup))

    if include_comment \
            and (constants.COMMENT_TEXT not in enabled_reactions) \
            and any((b for b in current_buttons if constants.COMMENT_TEXT in b.text)):
        enabled_reactions = enabled_reactions.copy()
        enabled_reactions.append(constants.COMMENT_TEXT)

    buttons_obj = []
    for r in enabled_reactions:
        cur_btn = next((b for b in current_buttons if r in b.text), None)
        if cur_btn is None:
            text = f'{r}'
            data = telegram_bot_utils.encode_button_data(handler=handler,
                                                         case_id=case_id,
                                                         response=r)
            cur_btn = types.InlineKeyboardButton(text=text,
                                                 callback_data=data)
        buttons_obj.append(cur_btn)
    return markup_from_buttons(buttons_obj)


def change_reaction_counter(reply_markup: types.InlineKeyboardMarkup, reaction: str, value: int, is_delta: bool):
    for btn in iterate_markup_buttons(reply_markup):
        if reaction in btn.text:
            prefix = btn.text.rstrip('0123456789-')

            if is_delta:
                old_num_str = btn.text.replace(prefix, '')
                old_num = _num_str_to_number(old_num_str)
                if old_num is None:
                    logger.error(f'Cannot parse button reaction state: {btn.text}')
                    continue
                num = old_num + value
            else:
                num = value
            new_num_str = '' if (num == 0) else f'{num}'

            t_new = f'{prefix}{new_num_str}'
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

