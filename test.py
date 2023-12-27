import os
import queue
import threading

import asyncio
import cv2
import face_recognition as fr
import numpy as np
from ENV import BOT_TOKEN, UNKNOWN_FACES_DIR_PATH, USER_ID
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from markups import stats_menu, confirm_add_student, settings_menu, tolerance_menu
from utils import clear_directory, unknown_faces_saver, unknown_faces_sender

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

face_queue = queue.Queue()
tolerance_queue = queue.Queue()
add_student = False
num_faces = 0
face_name = ''
name = ''
admin = USER_ID
tolerance = 0.6
unknown_face_num = -1
added_students_indexes = []
unknown_face_encodings = []


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Перезапустить бота"),
        types.BotCommand("stats", "Статистика"),
        types.BotCommand("settings", "Настройки"),
        types.BotCommand("unknown_faces", "Неизвестные лица"),
    ])


async def initialize_bot():
    await clear_directory(UNKNOWN_FACES_DIR_PATH)


def update_known_face_encodings():
    global unknown_face_encodings
    while True:
        try:

            face_data = face_queue.get(timeout=1)
            face_name, encoding, index = face_data

            known_face_names.append(face_name)
            known_face_encodings.append(encoding)

            added_face_names.append(face_name)
            added_face_encodings.append(encoding)

            np.save('datas/added_face_encodings.npy', added_face_encodings)
            np.save('datas/added_face_names.npy', added_face_names)

            print(f"Added student: {face_name}")

            added_students_indexes.append(index)
        except queue.Empty:
            pass


def update_tolerance():
    global tolerance
    while True:
        try:
            tolerance = tolerance_queue.get(timeout=1)
            print(f"Tolerance changed to {tolerance}")
        except queue.Empty:
            pass


update_thread = threading.Thread(target=update_known_face_encodings)
update_thread.start()

# Start a thread to update the tolerance parameter
tolerance_thread = threading.Thread(target=update_tolerance)
tolerance_thread.start()


async def reg_name(message):
    print(message)
    global face_name
    face_name = message.text

    await bot.send_message(admin,
                           f'Name of the newly added student is {face_name}, correct?',
                           reply_markup=confirm_add_student)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    global admin
    admin = USER_ID
    button1 = KeyboardButton(text="Текст кнопки 1")
    button2 = KeyboardButton(text="Текст кнопки 2")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button1).add(button2)
    await message.answer("Выбери опцию:", reply_markup=keyboard)

    await message.answer(f"Hello! I am a bot, which will provide statistics about students' attendance")


@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    await message.answer("What do you want to know?", reply_markup=stats_menu)


@dp.message_handler(commands=['settings'])
async def settings(message: types.Message):
    await message.answer("What setting do you want to change?", reply_markup=settings_menu)


@dp.message_handler(commands=['unknown_faces'])
async def unknown_faces(message: types.Message):
    if (len(unknown_face_encodings) == 0):
        await message.answer("No unknown faces detected")
    else:
        await message.answer("Here are the photos of unknown faces detected:")
        for k in range(len(unknown_face_encodings)):
            if k not in added_students_indexes:
                markup_inline_name_to_unknown = types.InlineKeyboardMarkup(row_width=1)
                item_add_student = types.InlineKeyboardButton(text='Add a student',
                                                              callback_data=f'add_student-{k}')
                markup_inline_name_to_unknown.add(item_add_student)

                with open(f'unknown_faces/unknown_face_{k}.jpg', 'rb') as photo:
                    await bot.send_photo(admin, photo, reply_markup=markup_inline_name_to_unknown)


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def check(message: types.Message):
    global add_student
    if add_student:
        await reg_name(message)


@dp.callback_query_handler(lambda call: True)
async def callback_query_handler(call: types.CallbackQuery):
    global add_student, unknown_face_num, tolerance, name

    if call.data == 'number_students':
        await bot.send_message(admin, f'{num_faces} faces detected')
    elif call.data == 'number_unknowns':
        await bot.send_message(admin, f'{len(unknown_face_encodings)} unknown faces are registered')

    elif call.data.startswith("add_student-"):
        unknown_face_num = int(call.data.split('-')[1])
        await bot.send_message(admin, "Enter a name of the student")
        add_student = True

    elif call.data == "yes":
        await bot.send_message(admin, 'The student is added')
        add_student = False

        student_face_encoding = unknown_face_encodings[unknown_face_num]
        face_queue.put((face_name, student_face_encoding, unknown_face_num))

    elif call.data == "no":
        await bot.send_message(admin, "Enter a name of the student")

    elif call.data == "change_tolerance":
        await bot.send_message(admin, f"Choose the tolerance (current is {tolerance})", reply_markup=tolerance_menu)

    elif call.data.startswith("0."):
        tolerance_queue.put(float(call.data))
        await bot.send_message(admin, f"Tolerance updated to {call.data}")


if os.path.exists('datas/added_face_encodings.npy'):
    known_face_encodings = np.load('datas/known_face_encodings.npy').tolist() + np.load(
        'datas/added_face_encodings.npy').tolist()
    known_face_names = np.load('datas/known_face_names.npy').tolist() + np.load('datas/added_face_names.npy').tolist()

    added_face_encodings = np.load('datas/added_face_encodings.npy').tolist()
    added_face_names = np.load('datas/added_face_names.npy').tolist()
else:
    known_face_encodings = np.load('datas/known_face_encodings.npy').tolist()
    known_face_names = np.load('datas/known_face_names.npy').tolist()

    added_face_encodings = []
    added_face_names = []

os.makedirs('unknown_faces', exist_ok=True)


def face_rec():
    global num_faces, admin

    set_default_commands(dp)

    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()
        face_locations = fr.face_locations(frame)
        face_encodings = fr.face_encodings(frame, face_locations)
        num_faces = len(face_locations)

        i = 0
        for face_encoding in face_encodings:

            matches = fr.compare_faces(known_face_encodings, face_encoding, tolerance=tolerance)

            unknown_face_matches = fr.compare_faces(unknown_face_encodings, face_encoding, tolerance=0.6)

            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            top, right, bottom, left = face_locations[i]

            if (name == "Unknown") and not (True in unknown_face_matches):
                face_image = frame[top:bottom, left:right]

                unknown_face_counter = len(unknown_face_encodings)

                unknown_faces_saver(face_image, unknown_face_counter)
                unknown_faces_sender(unknown_face_counter, bot, admin)

                unknown_face_encodings.append(face_encoding)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            i += 1

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


face_recognition_thread = threading.Thread(target=face_rec)
face_recognition_thread.start()
loop = asyncio.get_event_loop()
loop.run_until_complete(initialize_bot())
executor.start_polling(dp, skip_updates=True)
