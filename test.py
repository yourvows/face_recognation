import os
import queue
import threading
import aiohttp
import asyncio
import cv2
import face_recognition as fr
import numpy as np
from ENV import BOT_TOKEN, UNKNOWN_FACES_DIR_PATH, USER_ID, KNOWN_FACES_DIR
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.middlewares import BaseMiddleware
from markups import stats_menu, confirm_add_face, add_face_menu
from utils import clear_directory, unknown_faces_saver, unknown_faces_sender

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

face_queue = queue.Queue()
tolerance_queue = queue.Queue()
add_face = False
num_faces = 0
face_name = ''
name = ''
admin = USER_ID

unknown_face_num = -1
added_students_indexes = []
unknown_face_encodings = []
sended_photo = None
waiting_for_name = False


class LoggingMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):

        if message.photo:
            photo_id = message.photo[-1].file_id  # Получаем ID самой большой версии фотографии
            print(f" отправил фотографию с ID: {message.photo}")
        else:
            print(f"отправил сообщение: {message.text}")


dp.middleware.setup(LoggingMiddleware())


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Перезапустить бота"),
        types.BotCommand("stats", "Статистика"),
        types.BotCommand("unknown_faces", "Неизвестные лица"),
    ])


async def initialize_bot():
    await clear_directory(UNKNOWN_FACES_DIR_PATH)
    await set_default_commands(dp)


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

            added_students_indexes.append(index)
        except queue.Empty:
            pass


update_thread = threading.Thread(target=update_known_face_encodings)
update_thread.start()


async def reg_name(message):
    global face_name
    face_name = message.text

    await bot.send_message(admin,
                           f'Вы добавляете человека с именем: **{face_name}** ?',
                           reply_markup=confirm_add_face, parse_mode='Markdown')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    global admin
    admin = USER_ID

    await message.answer(f"Привет, {message.from_user.full_name}!\n"
                         f"Я бот который распознает лица в реальном времени.\n"
                         f"Чтобы воспользоваться моими функциями, используйте команды.\n")


@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    await message.answer("Выберите что вы хотите узнать", reply_markup=stats_menu)


@dp.message_handler(commands=['unknown_faces'])
async def unknown_faces(message: types.Message):
    if (len(unknown_face_encodings) == 0):
        await message.answer("Неизвестных лиц не обнаружено")
    else:
        await message.answer("Фотографии неизвестиных лиц:")
        for k in range(len(unknown_face_encodings)):
            if k not in added_students_indexes:
                markup_inline_name_to_unknown = types.InlineKeyboardMarkup(row_width=1)
                item_add_student = types.InlineKeyboardButton(text='Добавить лицо в бвзу данных',
                                                              callback_data=f'add_face-{k}')
                markup_inline_name_to_unknown.add(item_add_student)

                with open(f'unknown_faces/unknown_face_{k}.jpg', 'rb') as photo:
                    await bot.send_photo(admin, photo, reply_markup=markup_inline_name_to_unknown)


@dp.message_handler(content_types=types.ContentTypes.PHOTO)
async def handle_photo(message: types.Message):
    global sended_photo, waiting_for_name

    sended_photo = message.photo[-1].file_id
    waiting_for_name = True
    await message.reply("Введите имя для сохранения фотографии:", reply_markup=add_face_menu)


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_text(message: types.Message):
    global waiting_for_name, sended_photo, face_name, add_face
    if waiting_for_name:
        face_name = message.text
        waiting_for_name = False
        photo = await bot.get_file(sended_photo)
        download_path = os.path.join(KNOWN_FACES_DIR, f'{face_name}.jpg')
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{photo.file_path}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    with open(download_path, 'wb') as fd:
                        while True:
                            chunk = await resp.content.read(1024)
                            if not chunk:
                                break
                            fd.write(chunk)

        await message.reply(f"Фотография сохранена как: {face_name}.jpg")
        face_name = ''
        waiting_for_name = False
    elif add_face:
        await reg_name(message)


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def check(message: types.Message):
    global add_face
    if add_face:
        await reg_name(message)


@dp.callback_query_handler(lambda call: True)
async def callback_query_handler(call: types.CallbackQuery):
    global add_face, unknown_face_num, name, waiting_for_name, face_name

    if call.data == 'face_count':
        await bot.send_message(admin, f'{num_faces} обнаруженных лиц')
    elif call.data == 'unknown_faces_count':
        await bot.send_message(admin, f'{len(unknown_face_encodings)} неизвестных лиц')

    elif call.data.startswith("add_face-"):
        unknown_face_num = int(call.data.split('-')[1])
        await bot.send_message(admin, "Введите имя для сохранения фотографии:", reply_markup=add_face_menu)
        add_face = True

    elif call.data == "yes":
        await bot.send_message(admin, 'Лицо добавлено в базу данных')
        add_face = False

        student_face_encoding = unknown_face_encodings[unknown_face_num]
        face_queue.put((face_name, student_face_encoding, unknown_face_num))

    elif call.data == "no":
        await bot.send_message(admin, "Введите имя для сохранения фотографии:", reply_markup=add_face_menu)

    elif call.data == "cancel":
        add_face = False
        waiting_for_name = False
        face_name = ''
        await bot.send_message(admin, "Добавление отменено")


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

    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()
        face_locations = fr.face_locations(frame)
        face_encodings = fr.face_encodings(frame, face_locations)
        num_faces = len(face_locations)

        i = 0
        for face_encoding in face_encodings:

            matches = fr.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
            unknown_face_matches = fr.compare_faces(unknown_face_encodings, face_encoding, tolerance=0.6)

            name = "Unknown"
            color = (0, 0, 255)

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                color = (0, 255, 0)

            top, right, bottom, left = face_locations[i]

            if (name == "Unknown") and not (True in unknown_face_matches):
                face_image = frame[top:bottom, left:right]

                unknown_face_counter = len(unknown_face_encodings)

                unknown_faces_saver(face_image, unknown_face_counter)
                unknown_faces_sender(unknown_face_counter, bot, admin)

                unknown_face_encodings.append(face_encoding)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            i += 1

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


face_recognition_thread = threading.Thread(target=face_rec)
face_recognition_thread.start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialize_bot())
    executor.start_polling(dp, skip_updates=True)
