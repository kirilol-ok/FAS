# camera_input.py
import cv2 as cv
from qr_service import CodeDetector


class CameraInput:
    def __init__(self, camera_index: int = 0):
        self.cap = cv.VideoCapture(camera_index)
        self.code_detector = CodeDetector(multi_mode=False)

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
                    # TODO: send to API / start a worker thread / push to queue

                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                cv.imshow("frame", gray)

                if cv.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            self.cap.release()
            cv.destroyAllWindows()


if __name__ == "__main__":
    camera = CameraInput()
    camera.camera_capture()
