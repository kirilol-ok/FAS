"""
Camera input service updated for embedding comparison.

This module wraps OpenCV video capture logic and integrates QR code
detection with face verification.  When a QR code is scanned, the
service retrieves the stored face embedding associated with the QR code
and compares it to the embedding computed from the current frame.  The
previous implementation compared the frame against a stored image file;
this version eliminates the need to reconstruct the image and operates
directly on embeddings.

If ``expected_image_path`` is provided, the original image‑based
verification remains available.  Otherwise, if ``expected_image_hash``
is set and an ``ImageStorageService`` is supplied, the service will
fetch the embedding and perform an embedding comparison.
"""

from __future__ import annotations

import os
import time
from typing import Optional, Sequence, Tuple, Union

import cv2 as cv  # type: ignore

from .face_recognision_service import FaceRecognitionService
from .image_storage_service import ImageStorageService
from .qr_service import CodeDetector


class CameraInput:
    """Handle camera capture, QR detection and face verification."""

    def __init__(
        self,
        url: str = "http://host.docker.internal:8090/video",
        image_storage_service: Optional[ImageStorageService] = None,
        expected_image_hash: Optional[str] = None,
        expected_image_path: Optional[str] = None,
        verification_timeout: int = 5,
    ) -> None:
        # OpenCV capture object
        self.cap = cv.VideoCapture(url)
        # QR code detector
        self.code_detector = CodeDetector(multi_mode=False)
        # Face recognition service
        self.face_service = FaceRecognitionService()
        # Storage service for embeddings
        self.image_storage_service = image_storage_service
        # Expected image/embedding identifiers
        self.expected_image_hash = expected_image_hash or os.getenv(
            "EXPECTED_IMAGE_HASH"
        )
        self.expected_image_path = expected_image_path or os.getenv(
            "EXPECTED_IMAGE_PATH"
        )
        # Maximum time to wait after detecting a QR code for a successful match
        self.verification_timeout = verification_timeout

    def _get_reference(
        self,
    ) -> Optional[Tuple[str, Union[str, Tuple[bytes, str], Sequence[float]]]]:
        """
        Determine which reference data should be used for verification.

        The method prioritises an explicit file path over an embedding hash.
        Returns a tuple where the first element is a tag indicating the
        type ("path", "bytes", or "embedding") and the second element is
        the payload.  If no reference is available, returns ``None``.
        """
        # If a direct path is provided, use it first
        if self.expected_image_path:
            return ("path", self.expected_image_path)
        # Otherwise, attempt to resolve a hash via the storage service
        if self.expected_image_hash and self.image_storage_service:
            # Attempt to retrieve an embedding directly
            if hasattr(self.image_storage_service, "get_embedding_by_hash"):
                embedding = self.image_storage_service.get_embedding_by_hash(
                    self.expected_image_hash
                )
                if embedding:
                    return ("embedding", embedding)
            # Fall back to retrieving raw image bytes for backward compatibility
            if hasattr(self.image_storage_service, "get_image_bytes_by_hash"):
                image_data = self.image_storage_service.get_image_bytes_by_hash(
                    self.expected_image_hash
                )
                if image_data:
                    return ("bytes", image_data)
        return None

    def camera_capture(self) -> None:
        """Continuously capture frames, detect QR codes and verify faces."""
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Can't receive frame (stream end?).")
                # Detect a QR code in the current frame
                qr_text = self.code_detector.detect_qr(frame)
                if qr_text:
                    print(f"QR found: {qr_text}")
                    ref = self._get_reference()
                    if ref:
                        print("Starting face verification...")
                        verified = self._verify_face_after_qr(ref)
                        if verified:
                            print("Face verified successfully.")
                            break
                        else:
                            print("Face verification failed or timed out.")
                    else:
                        print("No reference configured; skipping face verification.")
                # Display the frame to the user
                cv.imshow("frame", frame)
                if cv.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            self.cap.release()
            cv.destroyAllWindows()

    def _verify_face_after_qr(
        self, ref: Tuple[str, Union[str, Tuple[bytes, str], Sequence[float]]]
    ) -> bool:
        """
        Attempt to verify the face within a limited time window after scanning a QR code.

        Depending on the type of reference, different verification strategies
        are used.  Embedding comparisons are preferred when available.
        """
        start_time = time.time()
        while time.time() - start_time < self.verification_timeout:
            ret, frame = self.cap.read()
            if not ret:
                break
            ref_type, payload = ref
            if ref_type == "path":
                try:
                    if self.face_service.verify_face(frame, payload):
                        return True
                except Exception as exc:
                    print(f"Error during face verification: {exc}")
            elif ref_type == "bytes":
                try:
                    data, mime = payload  # unpack tuple
                    if self.face_service.verify_face_with_bytes(frame, data, mime):
                        return True
                except Exception as exc:
                    print(f"Error during face verification: {exc}")
            elif ref_type == "embedding":
                try:
                    embedding = payload  # type: ignore[assignment]
                    if self.face_service.verify_face_with_embedding(frame, embedding):
                        return True
                except Exception as exc:
                    print(f"Error during embedding verification: {exc}")
            # Otherwise, continue until timeout
        return False


if __name__ == "__main__":
    # Example usage.  The ImageStorageService should be initialised with
    # an active SQLAlchemy session when using EXPECTED_IMAGE_HASH.  Here
    # we demonstrate reading the path/hash from environment variables only.
    camera = CameraInput()
    camera.camera_capture()
