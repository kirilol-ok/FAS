import importlib
import os
import sys
import types
from io import BytesIO

import numpy as np
import pytest


class DummyDeepFace:
    """A dummy DeepFace implementation used to stub out face verification."""

    def __init__(self, verified: bool = True) -> None:
        self._verified = verified

    def verify(
        self,
        img1_path: str,
        img2_path: str,
        model_name: str,
        detector_backend: str,
        distance_metric: str,
        enforce_detection: bool,
    ) -> dict:
        # return verification result according to the preset flag
        return {"verified": self._verified}

    def represent(self, *args, **kwargs):
        # return a fixed embedding representation regardless of input
        return [{"embedding": [1.0, 0.0]}]


@pytest.fixture
def face_service(monkeypatch):
    """
    Provide a FaceRecognitionService instance with the DeepFace dependency patched.

    The underlying module ``backend.services.face_recognision_service`` attempts to
    import the ``deepface`` library.  During tests we install a dummy
    implementation into ``sys.modules`` before loading the module so that the
    import succeeds and our dummy DeepFace is used.
    """
    # install dummy deepface module
    dummy_deepface_module = types.SimpleNamespace(DeepFace=DummyDeepFace())
    monkeypatch.setitem(sys.modules, "deepface", dummy_deepface_module)
    # reload the service module to pick up the dummy deepface
    module = importlib.reload(
        importlib.import_module("backend.services.face_recognision_service")
    )
    return module.FaceRecognitionService()


def create_test_frame() -> np.ndarray:
    """Generate a simple black image for use as a video frame."""
    return np.zeros((10, 10, 3), dtype=np.uint8)


def test_verify_face_returns_true_when_verified(monkeypatch, face_service):
    """verify_face should return True when DeepFace reports verification success."""
    # patch DummyDeepFace.verify to return a positive verification
    monkeypatch.setattr(
        DummyDeepFace, "verify", lambda self, **kwargs: {"verified": True}
    )
    frame = create_test_frame()
    # create a temporary reference file
    with open("/tmp/ref.jpg", "wb") as f:
        f.write(b"data")
    result = face_service.verify_face(frame, "/tmp/ref.jpg")
    assert result is True


def test_verify_face_returns_false_when_not_verified(monkeypatch, face_service):
    """verify_face should return False when DeepFace reports verification failure."""
    monkeypatch.setattr(
        DummyDeepFace, "verify", lambda self, **kwargs: {"verified": False}
    )
    frame = create_test_frame()
    with open("/tmp/ref2.jpg", "wb") as f:
        f.write(b"data")
    result = face_service.verify_face(frame, "/tmp/ref2.jpg")
    assert result is False


def test_verify_face_raises_value_error_for_invalid_arguments(face_service):
    """verify_face should raise when given a missing frame or reference path."""
    with pytest.raises(ValueError):
        face_service.verify_face(None, "somepath.jpg")
    with pytest.raises(ValueError):
        face_service.verify_face(create_test_frame(), "")


def test_verify_face_with_bytes_delegates_and_returns_true(monkeypatch, face_service):
    """verify_face_with_bytes should delegate to verify_face and return its result."""
    # patch verify_face to check the mime type is passed through and return True
    called = {}

    def dummy_verify_face(frame, ref_path):
        called["ref_path"] = ref_path
        return True

    monkeypatch.setattr(face_service, "verify_face", dummy_verify_face)
    frame = create_test_frame()
    sample_bytes = b"image"
    # call without specifying a mime type to exercise the default extension
    result = face_service.verify_face_with_bytes(frame, sample_bytes)
    assert result is True
    # ensure a temporary file path was passed to verify_face
    assert "ref_path" in called


def test_verify_face_with_bytes_raises_for_missing_inputs(face_service):
    """verify_face_with_bytes should raise for missing frame or bytes."""
    with pytest.raises(ValueError):
        face_service.verify_face_with_bytes(None, b"data")
    with pytest.raises(ValueError):
        face_service.verify_face_with_bytes(create_test_frame(), None)


def test_verify_face_with_embedding_returns_true_below_threshold(monkeypatch):
    """verify_face_with_embedding should return True when the distance is below the threshold."""
    # create a service with a high threshold to ensure success
    service_module = importlib.import_module(
        "backend.services.face_recognision_service"
    )
    service = service_module.FaceRecognitionService(threshold=0.5)
    # patch _compute_embedding_from_frame to return a deterministic embedding
    monkeypatch.setattr(
        service, "_compute_embedding_from_frame", lambda frame: [1.0, 0.0]
    )
    reference_embedding = [1.0, 0.0]
    frame = create_test_frame()
    assert service.verify_face_with_embedding(frame, reference_embedding) is True


def test_verify_face_with_embedding_returns_false_above_threshold(monkeypatch):
    """verify_face_with_embedding should return False when the distance exceeds the threshold."""
    service_module = importlib.import_module(
        "backend.services.face_recognision_service"
    )
    service = service_module.FaceRecognitionService(threshold=0.5)
    monkeypatch.setattr(
        service, "_compute_embedding_from_frame", lambda frame: [1.0, 0.0]
    )
    # reference embedding orthogonal to frame embedding yields cosine distance 1.0
    reference_embedding = [0.0, -1.0]
    frame = create_test_frame()
    assert service.verify_face_with_embedding(frame, reference_embedding) is False


def test_verify_face_with_embedding_raises_for_invalid_inputs(face_service):
    """verify_face_with_embedding should raise for missing frame or embedding."""
    with pytest.raises(ValueError):
        face_service.verify_face_with_embedding(None, [1, 2])
    with pytest.raises(ValueError):
        face_service.verify_face_with_embedding(create_test_frame(), None)
