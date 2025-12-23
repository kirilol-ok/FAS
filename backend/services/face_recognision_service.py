import cv2

from cv2 import VideoCapture
from dotenv import load_dotenv
from deepface import DeepFace

backends = [
  'opencv'
]

class FaceRecogniser():
    def __init__(self):
        return
    def detect_face_livestream(self) -> bool:
        DeepFace.stream(
            db_path="database_folder",
            detector_backend=backends[1], 
            enable_face_analysis=True,
            anti_spoofing=True
                            )
        
