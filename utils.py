import os
import shutil
import cv2
import sys


async def clear_directory(directory_path):
    if not os.path.exists(directory_path):
        return

    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error clearing file or directory {file_path}: {e}")

    print(f"Directory '{directory_path}' cleared successfully.")


def unknown_faces_saver(face_image, unknown_face_counter):
    file_directory = 'unknown_faces'
    os.makedirs(file_directory, exist_ok=True)
    filename = os.path.join(file_directory, f'unknown_face_{unknown_face_counter}.jpg')
    cv2.imwrite(filename, face_image)


async def unknown_faces_sender(unknown_face_counter, bot, admin):
    filename = os.path.join('unknown_faces', f'unknown_face_{unknown_face_counter}.jpg')
    if os.path.exists(filename):
        with open(filename, 'rb') as photo:
            await bot.send_photo(admin, photo)
        await bot.send_message(admin, 'Unknown face detected')
    else:
        print(f"File {filename} not found.")
