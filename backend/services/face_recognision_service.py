from __future__ import annotations

import os
import tempfile
from typing import Optional, Sequence

import cv2 as cv
import numpy as np
from deepface import DeepFace


class FaceRecognitionService:
    def __init__(
        self,
        model_name: str = "VGG-Face",
        detector_backend: str = "opencv",
        distance_metric: str = "cosine",
        threshold: Optional[float] = None,
    ) -> None:
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric

        # Default threshold calibrated for VGG-Face and cosine distance
        if threshold is None:
            self.threshold = 0.40 if distance_metric == "cosine" else 0.60
        else:
            self.threshold = threshold

    def preload_model(self) -> None:
        build_model = getattr(DeepFace, "build_model", None)
        if callable(build_model):
            build_model(self.model_name)

        build_detector = getattr(DeepFace, "build_detector", None)
        if callable(build_detector):
            build_detector(self.detector_backend)

    def _compute_embedding_from_frame(self, frame) -> list[float]:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            cv.imwrite(tmp_file.name, frame)
            frame_path = tmp_file.name

        try:
            representations = DeepFace.represent(
                img_path=frame_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False,
            )
            if not representations:
                raise ValueError("No face embedding could be extracted from the frame")
            embedding = representations[0]["embedding"]
            return list(embedding)
        finally:
            try:
                os.unlink(frame_path)
            except OSError:
                pass

    def _compute_distance(self, emb1: Sequence[float], emb2: Sequence[float]) -> float:
        v1 = np.array(emb1, dtype=float)
        v2 = np.array(emb2, dtype=float)

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return float("inf")

        similarity = np.dot(v1, v2) / (norm1 * norm2)
        return 1.0 - float(similarity)  # cosine distance

    def verify_face(self, frame, reference_image_path: str) -> bool:
        if frame is None or not reference_image_path:
            raise ValueError("Frame and reference image path must be provided")

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

        ext = None
        if mime_type:
            import mimetypes

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

    def verify_face_with_embedding(
        self,
        frame,
        reference_embedding: Sequence[float],
        threshold: Optional[float] = None,
    ) -> bool:
        if frame is None or reference_embedding is None:
            raise ValueError("Frame and reference embedding must be provided")

        try:
            frame_embedding = self._compute_embedding_from_frame(frame)
        except Exception:
            return False

        distance = self._compute_distance(frame_embedding, reference_embedding)
        effective_threshold = threshold if threshold is not None else self.threshold
        return distance <= effective_threshold
