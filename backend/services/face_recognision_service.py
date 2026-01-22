"""
Face recognition service with embedding support.

This service augments the original face recognition implementation
by exposing methods that operate directly on precomputed embeddings.
It still retains compatibility with the original image-based verification
methods but adds an efficient embedding-based comparison routine.

The DeepFace library is used to generate embeddings for both stored
reference images and incoming frames. To compare two embeddings, the
cosine distance is computed and a configurable threshold is applied.
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional, Sequence

import cv2 as cv  # type: ignore
import numpy as np  # type: ignore
from deepface import DeepFace  # type: ignore


class FaceRecognitionService:
    """Service for verifying faces using DeepFace embeddings."""

    def __init__(
        self,
        model_name: str = "VGG-Face",
        detector_backend: str = "opencv",
        distance_metric: str = "cosine",
        threshold: Optional[float] = None,
    ) -> None:
        """
        Initialise the face recognition service.

        Parameters
        ----------
        model_name : str, optional
            The name of the DeepFace model to use for embedding extraction.
        detector_backend : str, optional
            The backend detector used by DeepFace.
        distance_metric : str, optional
            The metric to use when comparing embeddings. Currently only
            "cosine" is supported for custom embedding comparison.
        threshold : float, optional
            Override the default decision threshold for the distance metric.
            If not provided, a sensible default based on the model and metric
            will be used (0.40 for cosine on VGG-Face).
        """
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric

        # Default threshold calibrated for VGG-Face and cosine distance
        if threshold is None:
            self.threshold = 0.40 if distance_metric == "cosine" else 0.60
        else:
            self.threshold = threshold

    def preload_model(self) -> None:
        """Preload DeepFace model (and detector, if available).

        The FastAPI app calls `preload_model` on startup to avoid a cold start.
        DeepFace internally caches built models, so invoking build helpers here
        speeds up the first real verification request.
        """
        build_model = getattr(DeepFace, "build_model", None)
        if callable(build_model):
            build_model(self.model_name)

        # Some DeepFace versions expose detector warm-up as build_detector
        build_detector = getattr(DeepFace, "build_detector", None)
        if callable(build_detector):
            build_detector(self.detector_backend)

    def _compute_embedding_from_frame(self, frame) -> list[float]:
        """
        Compute a face embedding from an in-memory video frame.

        The frame is written to a temporary JPEG file because DeepFace
        operates on file paths. Detection is not enforced to avoid
        unnecessary errors when no face is present; such cases will be
        handled by the caller.
        """
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
        """Compute the cosine distance between two embeddings."""
        v1 = np.array(emb1, dtype=float)
        v2 = np.array(emb2, dtype=float)

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return float("inf")

        similarity = np.dot(v1, v2) / (norm1 * norm2)
        return 1.0 - float(similarity)  # cosine distance

    def verify_face(self, frame, reference_image_path: str) -> bool:
        """
        Delegate verification to DeepFace using image paths.

        This preserves the original behaviour: two image files are compared
        directly by DeepFace, which manages thresholds internally.
        """
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
        """
        Verify a face using raw bytes for the reference image.

        Writes the reference bytes to a temporary file and delegates to verify_face.
        """
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
        """
        Verify a face by comparing embeddings.

        Returns True if the cosine distance between embeddings is below the threshold.
        """
        if frame is None or reference_embedding is None:
            raise ValueError("Frame and reference embedding must be provided")

        try:
            frame_embedding = self._compute_embedding_from_frame(frame)
        except Exception:
            return False

        distance = self._compute_distance(frame_embedding, reference_embedding)
        effective_threshold = threshold if threshold is not None else self.threshold
        return distance <= effective_threshold
