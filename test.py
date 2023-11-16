import os

import asyncio
import cv2
import face_recognition as fr
from aiogram import Bot, Dispatcher

TOKEN = '5746482080:AAEXD3ufpUKUJ0Pgj0ofJapVCycGLxFF11k'
USER_ID = '837097830'

bot = Bot(TOKEN)
dp = Dispatcher(bot)

known_faces_folder = "known_faces"
known_face_encodings = []
known_face_names = []

for filename in os.listdir(known_faces_folder):
    if filename.endswith((".jpg", ".png")):
        image_path = os.path.join(known_faces_folder, filename)
        image = fr.load_image_file(image_path)

        face_encoding = fr.face_encodings(image)[0]
        known_face_encodings.append(face_encoding)
        known_face_names.append(os.path.splitext(filename)[0])


async def send_photo(photo_path):
    with open(photo_path, 'rb') as photo:
        await bot.send_photo(chat_id=USER_ID, photo=photo)


async def process_frame(frame):
    face_locations = fr.face_locations(frame, model="cnn")
    face_encodings = []

    for face_location in face_locations:
        top, right, bottom, left = face_location
        face_image = frame[top:bottom, left:right]

        try:
            face_encoding = fr.face_encodings(face_image)[0]
            face_encodings.append(face_encoding)
        except IndexError:
            print("No face found in the given image.")

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = fr.compare_faces(known_face_encodings, face_encoding)
        top, right, bottom, left = face_location

        color = (0, 255, 0) if any(matches) else (0, 0, 255)
        matched_names = [known_face_names[i] for i, match in enumerate(matches) if match]

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        for name in matched_names:
            cv2.putText(frame, name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if not any(matches):
            face_image = frame[top:bottom, left:right]
            cv2.imwrite('unknown_face.jpg', face_image)
            await send_photo('unknown_face.jpg')


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
    asyncio.ensure_future(main())
    loop.run_forever()

# TOKEN = '5746482080:AAEXD3ufpUKUJ0Pgj0ofJapVCycGLxFF11k'
# USER_ID = '837097830'
