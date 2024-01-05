from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

stats_menu = InlineKeyboardMarkup(row_width=1)
total_face_count = InlineKeyboardButton(text='Количество обнаруженных лиц', callback_data='face_count')
total_unknown_face_count = InlineKeyboardButton(text='Количество не распознанных лиц',
                                                callback_data='unknown_faces_count')
stats_menu.add(total_face_count, total_unknown_face_count)

add_face_menu = InlineKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
cencel_add_face = InlineKeyboardButton(text='Отмена', callback_data='cancel')
add_face_menu.add(cencel_add_face)

confirm_add_face = InlineKeyboardMarkup(row_width=2)
item_yes = InlineKeyboardButton(text="Да", callback_data='yes')
item_no = InlineKeyboardButton(text="Нет", callback_data='no')
confirm_add_face.add(item_yes, item_no)
