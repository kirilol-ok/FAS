# camera_input.py
import cv2 as cv
from qr_service import CodeDetector
from time import time


class CameraInput:
    def __init__(self, camera_index: int = 0):
        self.cap = cv.VideoCapture(camera_index)
        self.code_detector = CodeDetector(multi_mode=False)
        self.face_req = False
        self.timeout = 5 # time in seconds

    def camera_capture(self) -> None:
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Can't receive frame (stream end?).")

                qr_text = self.code_detector.detect_qr(frame)
                if qr_text:
                    print(f"QR found: {qr_text}")
                    self.face_req = True

                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                cv.imshow("frame", gray)

                # Face recognision thread
                if self.face_req:
                    self.cap.release()
                    time_start = time()
                    while time() < time_start + self.timeout:
                        return


                if cv.waitKey(1) & 0xFF == ord("q"):
                    break

        finally:
            self.cap.release()
            cv.destroyAllWindows()


if __name__ == "__main__":
    camera = CameraInput()
    camera.camera_capture()
