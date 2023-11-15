import asyncio
import cv2
import face_recognition as fr
from PIL import Image
from aiogram import Bot, Dispatcher

TOKEN = '5746482080:AAEXD3ufpUKUJ0Pgj0ofJapVCycGLxFF11k'
USER_ID = '837097830'

bot = Bot(TOKEN)
dp = Dispatcher(bot)

picture_of_me = fr.load_image_file("me.jpg")
my_face_encoding = fr.face_encodings(picture_of_me)[0]


async def send_photo(photo_path):
    print("Face is not recognized")
    with open(photo_path, 'rb') as photo:
        await bot.send_photo(chat_id=USER_ID, photo=photo)


known_face_encodings = [my_face_encoding]
known_face_names = ['Ibrohim']


async def process_frame(frame):
    face_locations = fr.face_locations(frame)
    face_encodings = fr.face_encodings(frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        is_match = fr.compare_faces(known_face_encodings, face_encoding)
        top, right, bottom, left = face_location
        if any(is_match):

            matched_name = known_face_names[is_match.index(True)]
            color = (0, 255, 0)
        else:
            matched_name = 'UNKNOWN'
            color = (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, matched_name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        if not any(is_match):
            face_image = frame[top:bottom, left:right]
            pil_image = Image.fromarray(face_image)
            pil_image.save('unknown_face.jpg')
            await send_photo('unknown_face.jpg')


async def on_startup():
    await bot.send_message(chat_id=USER_ID, text='Bot has been started')


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
