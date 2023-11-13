import asyncio
import cv2
import face_recognition as fr
import numpy as np
from PIL import Image
from aiogram import Bot, Dispatcher

TOKEN = 'TELEGRAM_BOT_TOKEN'

bot = Bot(TOKEN)
dp = Dispatcher(bot)
user_id = 'USER_ID'

picture_of_me = fr.load_image_file("YOUR_IMAGE")
my_face_encoding = fr.face_encodings(picture_of_me)[0]


async def send_photo(photo_path):
    print("Face is not recognized")
    with open(photo_path, 'rb') as photo:
        await bot.send_photo(chat_id=user_id, photo=photo)


async def process_frame(frame):
    face_locations = fr.face_locations(frame)

    for face_encoding in fr.face_encodings(frame, face_locations):

        is_match = fr.compare_faces([np.array(my_face_encoding)], np.array(face_encoding))
        if is_match[0]:
            continue
        else:
            for face_location in face_locations:
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                face_image = frame[top:bottom, left:right]
                pil_image = Image.fromarray(face_image)
                pil_image.save('unknown_face.jpg')

            await send_photo('unknown_face.jpg')


async def on_startup():
    await bot.send_message(chat_id=user_id, text='Bot has been started')


async def main():
    video_capture = cv2.VideoCapture(0)

    try:
        while True:
            ret, frame = video_capture.read()
            face_locations = fr.face_locations(frame)
            for face_location in face_locations:
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            await process_frame(frame)
            cv2.imshow('Video', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        video_capture.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    asyncio.ensure_future(main())
    loop.run_forever()
