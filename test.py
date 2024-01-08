import os
import queue
import threading
import aiohttp
import asyncio
import cv2
import face_recognition as fr
import numpy as np
from env import BOT_TOKEN, UNKNOWN_FACES_DIR_PATH, USER_ID, KNOWN_FACES_DIR
from aiogram import Bot, types, Dispatcher, executor
from markups import create_stats_menu, create_confirm_add_face_menu, create_add_face_menu
from utils import clear_directory, save_unknown_face, send_unknown_face

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

face_queue = queue.Queue()
is_add_face_mode_active = False
detected_face_count = 0
face_name = ''
name = ''
selected_unknown_face_index = -1
added_students_indexes = []
unknown_face_encodings = []
sent_photo = None
waiting_for_name = False


def is_allowed_user(message: types.Message):
    """Check if the message is from the allowed user."""
    return message.from_user.id == int(USER_ID)


def allowed_user_only(handler):
    """Decorator to restrict access to a handler to only the allowed user."""

    async def wrapper(message: types.Message, *args, **kwargs):
        if message.from_user.id != int(USER_ID):
            return
        return await handler(message, *args, **kwargs)

    return wrapper


async def initialize_bot():
    await clear_directory(UNKNOWN_FACES_DIR_PATH)
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Запустить бота"),
        types.BotCommand("add_unknown_faces", "Добавить неизвестные лица"),
    ])


def run_coroutine_threadsafe(coro, loop):
    asyncio.run_coroutine_threadsafe(coro, loop)


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


async def register_face_name(message):
    global face_name
    face_name = message.text
    await bot.send_message(USER_ID,
                           f'Вы добавляете человека с именем: **{face_name}** ?',
                           reply_markup=create_confirm_add_face_menu(),
                           parse_mode='Markdown'
                           )


@dp.message_handler(commands=['start'])
@allowed_user_only
async def start(message: types.Message, **kwargs):
    if not is_allowed_user(message):
        await message.answer("Вы не имеете доступа к этому боту")
        return
    await message.answer(f"Привет, {message.from_user.full_name}!\n"
                         f"Я бот который распознает лица в реальном времени.\n"
                         f"Чтобы воспользоваться моими функциями, используйте команды.\n")


@dp.message_handler(commands=['stats'])
@allowed_user_only
async def stats(message: types.Message, **kwargs):
    await message.answer("Выберите что вы хотите узнать", reply_markup=create_stats_menu())


def create_unknown_faces_markup(index):
    markup = types.InlineKeyboardMarkup(row_width=1)
    add_student_button = types.InlineKeyboardButton(text='Добавить лицо в базу данных',
                                                    callback_data=f'add_face-{index}')
    markup.add(add_student_button)
    return markup


@dp.message_handler(commands=['add_unknown_faces'])
@allowed_user_only
async def add_unknown_faces(message: types.Message, **kwargs):
    if not unknown_face_encodings:
        await message.answer("Неизвестных лиц не обнаружено")
    else:
        await message.answer("Фотографии неизвестных лиц:")
        for k, encoding in enumerate(unknown_face_encodings):
            if k not in added_students_indexes:
                markup = create_unknown_faces_markup(k)
                photo_path = f'unknown_faces/unknown_face_{k}.jpg'
                with open(photo_path, 'rb') as photo:
                    await bot.send_photo(USER_ID, photo, reply_markup=markup)


@dp.message_handler(content_types=types.ContentTypes.PHOTO)
async def handle_photo(message: types.Message):
    global sent_photo, waiting_for_name

    sent_photo = message.photo[-1].file_id
    waiting_for_name = True
    await message.reply("Введите имя для сохранения фотографии:", reply_markup=create_add_face_menu())


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_text(message: types.Message):
    global waiting_for_name, sent_photo, face_name, is_add_face_mode_active
    if waiting_for_name:
        face_name = message.text
        waiting_for_name = False
        photo = await bot.get_file(sent_photo)
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
    elif is_add_face_mode_active:
        await register_face_name(message)


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def check(message: types.Message):
    global is_add_face_mode_active
    if is_add_face_mode_active:
        await register_face_name(message)


async def handle_add_face(call_data):
    selected_unknown_face_index = int(call_data.split('-')[1])
    await bot.send_message(USER_ID, "Введите имя для сохранения фотографии:", reply_markup=create_add_face_menu())
    global is_add_face_mode_active
    is_add_face_mode_active = True


async def handle_yes():
    await bot.send_message(USER_ID, 'Лицо добавлено в базу данных')
    global is_add_face_mode_active, selected_unknown_face_index, face_name
    is_add_face_mode_active = False
    student_face_encoding = unknown_face_encodings[selected_unknown_face_index]
    face_queue.put((face_name, student_face_encoding, selected_unknown_face_index))


async def handle_no():
    await bot.send_message(USER_ID, "Введите имя для сохранения фотографии:", reply_markup=create_add_face_menu())


async def handle_cancel():
    global is_add_face_mode_active, waiting_for_name, face_name
    is_add_face_mode_active = False
    waiting_for_name = False
    face_name = ''
    await bot.send_message(USER_ID, "Добавление отменено")


callback_actions = {
    'yes': handle_yes,
    'no': handle_no,
    'cancel': handle_cancel,
}


@dp.callback_query_handler(lambda call: True)
async def callback_query(call: types.CallbackQuery):
    action = call.data
    if action.startswith("add_face-"):
        await handle_add_face(action)
    else:
        handler = callback_actions.get(action)
        if handler:
            await handler()


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


def start_face_recognition(loop):
    global detected_face_count, USER_ID

    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()
        face_locations = fr.face_locations(frame)
        face_encodings = fr.face_encodings(frame, face_locations)
        detected_face_count = len(face_locations)

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

                save_unknown_face(face_image, unknown_face_counter)
                run_coroutine_threadsafe(send_unknown_face(unknown_face_counter, bot, USER_ID), loop)

                unknown_face_encodings.append(face_encoding)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            i += 1

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    face_recognition_thread = threading.Thread(target=start_face_recognition, args=(loop,))
    face_recognition_thread.start()
    loop.run_until_complete(initialize_bot())
    executor.start_polling(dp, skip_updates=True)
