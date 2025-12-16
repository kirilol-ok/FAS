# qr_service.py
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

        text, points, _ = self.detector.detectAndDecode(frame)
        return text if text else None

    def detect_qr_with_points(self, frame) -> Tuple[Optional[str], Optional[np.ndarray]]:
        if frame is None:
            return None, None

        text, points, _ = self.detector.detectAndDecode(frame)
        if not text:
            return None, None
        return text, points

    @staticmethod
    def draw_bbox(frame, points, color=(0, 255, 0), thickness: int = 3):
        if points is None:
            return frame
        pts = points.astype(int).reshape(-1, 2)
        cv.polylines(frame, [pts], isClosed=True, color=color, thickness=thickness)
        return frame
