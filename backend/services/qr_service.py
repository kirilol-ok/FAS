import cv2 as cv
import numpy as np
from typing import Optional, Tuple


class CodeDetector:
    def __init__(self, multi_mode: bool = False):
        self.detector = cv.QRCodeDetector()
        self.multi_mode = multi_mode

    def detect_qr(self, frame) -> Optional[str]:
        if frame is None:
            return None

        if self.multi_mode:
            ok, decoded_list, points, _ = self.detector.detectAndDecodeMulti(frame)
            if not ok or not decoded_list:
                return None
            for text in decoded_list:
                if text:
                    return text
            return None

        text, _, _ = self.detector.detectAndDecode(frame)
        return text if text else None

    def detect_qr_with_points(self, frame) -> Tuple[Optional[str], Optional[np.ndarray]]:
        if frame is None:
            return None, None
        text, points, _ = self.detector.detectAndDecode(frame)
        if not text:
            return None, None
        return text, points


def decode_qr_from_bytes(image_bytes: bytes) -> Optional[str]:
    """
    Decode QR code from raw bytes (typically uploaded files).
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv.imdecode(nparr, cv.IMREAD_COLOR)
        if img is None:
            return None
        detector = CodeDetector()
        return detector.detect_qr(img)
    except Exception as e:
        print(f"Error processing image: {e}")
        return None