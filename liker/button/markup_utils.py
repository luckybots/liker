from telebot import types
from typing import Optional
from tengine import telegram_utils


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

    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(*buttons_obj)
    return reply_markup
