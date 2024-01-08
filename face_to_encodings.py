import os

import face_recognition as fr
import numpy as np
from env import KNOWN_FACES_DIR, KNOWN_FACE_NAMES_PATH, KNOWN_ENCODINGS_PATH

known_face_encodings = []
known_face_names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith((".jpg", ".png")):
        image_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = fr.load_image_file(image_path)
        face_encoding = fr.face_encodings(image)[0]
        known_face_encodings.append(face_encoding)
        known_face_names.append(os.path.splitext(filename)[0])

np.save(KNOWN_ENCODINGS_PATH, known_face_encodings)
np.save(KNOWN_FACE_NAMES_PATH, known_face_names)
