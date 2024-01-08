from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_stats_menu():
    stats_menu = InlineKeyboardMarkup(row_width=1)
    button_face_count = InlineKeyboardButton(text='Количество обнаруженных лиц', callback_data='face_count')
    button_unknown_faces_count = InlineKeyboardButton(text='Количество не распознанных лиц',
                                                      callback_data='unknown_faces_count')
    stats_menu.add(button_face_count, button_unknown_faces_count)
    return stats_menu


def create_add_face_menu():
    add_face_menu = InlineKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    button_cancel_add_face = InlineKeyboardButton(text='Отмена', callback_data='cancel')
    add_face_menu.add(button_cancel_add_face)
    return add_face_menu


def create_confirm_add_face_menu():
    confirm_add_face = InlineKeyboardMarkup(row_width=2)
    button_yes = InlineKeyboardButton(text="Да", callback_data='yes')
    button_no = InlineKeyboardButton(text="Нет", callback_data='no')
    confirm_add_face.add(button_yes, button_no)
    return confirm_add_face
