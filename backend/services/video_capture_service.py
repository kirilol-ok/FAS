from __future__ import annotations

import os
import time
import tempfile
from typing import Optional, Tuple, Union

import cv2 as cv

from .face_recognision_service import FaceRecognitionService
from .image_storage_service import ImageStorageService
from .qr_service import CodeDetector


class CameraInput:
    def __init__(
        self,
        camera_index: int = 0,
        image_storage_service: Optional[ImageStorageService] = None,
        expected_image_hash: Optional[str] = None,
        expected_image_path: Optional[str] = None,
        verification_timeout: int = 5,
    ) -> None:
        self.cap = cv.VideoCapture(camera_index)
        self.code_detector = CodeDetector(multi_mode=False)
        self.face_service = FaceRecognitionService()
        self.image_storage_service = image_storage_service
        self.expected_image_hash = expected_image_hash or os.getenv("EXPECTED_IMAGE_HASH")
        self.expected_image_path = expected_image_path or os.getenv("EXPECTED_IMAGE_PATH")
        self.verification_timeout = verification_timeout

    def _get_reference_image(self) -> Optional[Tuple[str, Union[str, Tuple[bytes, str]]]]:
        # Priority: explicit path > environment path > hash
        if self.expected_image_path:
            return ("path", self.expected_image_path)

        if self.expected_image_hash and self.image_storage_service:
            image_data = self.image_storage_service.get_image_bytes_by_hash(self.expected_image_hash)
            if image_data:
                return ("bytes", image_data)
        return None

    def camera_capture(self) -> None:
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Can't receive frame (stream end?).")
                # Detect QR code
                qr_text = self.code_detector.detect_qr(frame)
                if qr_text:
                    print(f"QR found: {qr_text}")
                    ref = self._get_reference_image()
                    if ref:
                        print("Starting face verification...")
                        verified = self._verify_face_after_qr(ref)
                        if verified:
                            print("Face verified successfully.")
                            break
                        else:
                            print("Face verification failed or timed out.")
                    else:
                        print("No reference image configured; skipping face verification.")
                cv.imshow("frame", frame)
                if cv.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            self.cap.release()
            cv.destroyAllWindows()

    def _verify_face_after_qr(self, ref: Tuple[str, Union[str, Tuple[bytes, str]]]) -> bool:
        start_time = time.time()
        while time.time() - start_time < self.verification_timeout:
            ret, frame = self.cap.read()
            if not ret:
                break
            if ref[0] == "path":
                try:
                    if self.face_service.verify_face(frame, ref[1]):
                        return True
                except Exception as exc:
                    print(f"Error during face verification: {exc}")
            elif ref[0] == "bytes":
                try:
                    data, mime = ref[1]  # unpack tuple
                    if self.face_service.verify_face_with_bytes(frame, data, mime):
                        return True
                except Exception as exc:
                    print(f"Error during face verification: {exc}")
            # otherwise continue
        return False


if __name__ == "__main__":
    # Example usage.  The ImageStorageService should be initialized with
    # an active SQLAlchemy session when using EXPECTED_IMAGE_HASH.  Here
    # we demonstrate reading the path/hash from environment variables only.
    camera = CameraInput()
    camera.camera_capture()