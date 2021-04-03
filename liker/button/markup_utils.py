from telebot import types
from typing import Optional
from tengine import telegram_utils


# def _build_reply_markup(buttons: Collection[str],
#                         buttons_data: Collection[str],
#                         buttons_columns: int):
#     reply_markup = None
#     if buttons is not None:
#         if buttons_data is None:
#             buttons_data = buttons
#         assert len(buttons) == len(buttons_data), \
#             f'Buttons & buttons data size mismatch: {len(buttons)} != {len(buttons_data)}'
#
#         reply_markup = types.InlineKeyboardMarkup()
#
#         buttons_obj = [types.InlineKeyboardButton(text=text, callback_data=data)
#                        for text, data in zip(buttons, buttons_data)]
#         buttons_rows = list(chunks(buttons_obj, n=buttons_columns))
#
#         for row in buttons_rows:
#             reply_markup.add(*row)
#     return reply_markup

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

    # TODO: handle message_dict['urls']

    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(*buttons_obj)
    return reply_markup
