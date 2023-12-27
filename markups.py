from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

stats_menu = InlineKeyboardMarkup(row_width=1)
item_number_of_students = InlineKeyboardButton(text='Number of students', callback_data='number_students')
item_number_of_unknown_faces = InlineKeyboardButton(text='Number of unknown faces registered',
                                                    callback_data='number_unknowns')
stats_menu.add(item_number_of_students, item_number_of_unknown_faces)

confirm_add_student = InlineKeyboardMarkup(row_width=2)
item_yes = InlineKeyboardButton(text="Yes", callback_data='yes')
item_no = InlineKeyboardButton(text="No", callback_data='no')
confirm_add_student.add(item_yes, item_no)

settings_menu = InlineKeyboardMarkup(row_width=1)
item_tolerance = InlineKeyboardButton(text="Tolerance", callback_data='change_tolerance')
settings_menu.add(item_tolerance)

tolerance_menu = InlineKeyboardMarkup(row_width=3)
item_1 = InlineKeyboardButton(text='0.1', callback_data='0.1')
item_2 = InlineKeyboardButton(text='0.2', callback_data='0.2')
item_3 = InlineKeyboardButton(text='0.3', callback_data='0.3');
item_4 = InlineKeyboardButton(text='0.4', callback_data='0.4')
item_5 = InlineKeyboardButton(text='0.5', callback_data='0.5')
item_6 = InlineKeyboardButton(text='0.6', callback_data='0.6')
item_7 = InlineKeyboardButton(text='0.7', callback_data='0.7')
item_8 = InlineKeyboardButton(text='0.8', callback_data='0.8')
item_9 = InlineKeyboardButton(text='0.9', callback_data='0.9')
tolerance_menu.add(item_1, item_2, item_3, item_4, item_5, item_6, item_7, item_8, item_9)
