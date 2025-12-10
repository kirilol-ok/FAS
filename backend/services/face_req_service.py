import cv2
import mediapipe as mp

from mediapipe.tasks.python import vision
from mediapipe.tasks import python
from dotenv import load_dotenv

model_path = "/app/backend/detection_LLM/blaze_face_short_range.tflite"

BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Create a face detector instance with the image mode:
options = FaceDetectorOptions(
    base_options=BaseOptions(model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,)
with FaceDetector.create_from_options(options) as detector:
  # The detector is initialized. Use it here.
  # ...
  