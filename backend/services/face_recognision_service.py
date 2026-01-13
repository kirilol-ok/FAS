from __future__ import annotations

import os
import tempfile
from typing import Optional

import cv2 as cv
from deepface import DeepFace


class FaceRecognitionService:
    def __init__(
        self,
        model_name: str = "VGG-Face",
        detector_backend: str = "opencv",
        distance_metric: str = "cosine",
    ) -> None:
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric

    def verify_face(self, frame, reference_image_path: str) -> bool:
        if frame is None or not reference_image_path:
            raise ValueError("Frame and reference image path must be provided")

        # Save the current frame to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_frame:
            cv.imwrite(tmp_frame.name, frame)
            frame_path = tmp_frame.name

        try:
            result = DeepFace.verify(
                img1_path=frame_path,
                img2_path=reference_image_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                distance_metric=self.distance_metric,
                enforce_detection=False,
            )
            return bool(result.get("verified"))
        finally:
            try:
                os.unlink(frame_path)
            except OSError:
                pass

    def verify_face_with_bytes(
        self,
        frame,
        reference_image_bytes: bytes,
        mime_type: Optional[str] = None,
    ) -> bool:
        
        if frame is None or reference_image_bytes is None:
            raise ValueError("Frame and reference image bytes must be provided")

        # Determine a file extension based on the mime type
        ext = None
        if mime_type:
            import mimetypes  # local import to avoid top-level dependency
            ext = mimetypes.guess_extension(mime_type)
        if not ext:
            ext = ".jpg"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_ref:
            tmp_ref.write(reference_image_bytes)
            ref_path = tmp_ref.name

        try:
            return self.verify_face(frame, ref_path)
        finally:
            try:
                os.unlink(ref_path)
            except OSError:
                pass