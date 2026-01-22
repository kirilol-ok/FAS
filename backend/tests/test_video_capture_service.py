import importlib
import sys
import types

import pytest


class DummyDeepFace:
    """Stand-in for the DeepFace library to allow importing face_recognision_service."""

    def verify(self, *args, **kwargs):
        return {"verified": True}


class DummyFaceService:
    """Simple fake face recognition service with configurable results."""

    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.called_with = []

    def verify_face(self, frame, path: str) -> bool:
        self.called_with.append(("face", frame, path))
        return self.result

    def verify_face_with_bytes(self, frame, data: bytes, mime: str) -> bool:
        self.called_with.append(("bytes", frame, data, mime))
        return self.result

    def verify_face_with_embedding(self, frame, embedding):
        self.called_with.append(("embedding", frame, embedding))
        return self.result


class DummyCap:
    """Fake video capture object returning a fixed frame until exhausted."""

    def __init__(self, reads: int = 5) -> None:
        self.reads = reads
        self.calls = 0

    def isOpened(self) -> bool:
        return True

    def read(self):
        if self.calls < self.reads:
            self.calls += 1
            return True, "frame"
        # simulate end of stream
        return False, None

    def release(self) -> None:
        pass


@pytest.fixture(autouse=True)
def video_module(monkeypatch):
    """
    Provide a freshly imported video_capture_service module with patched dependencies.

    This fixture installs a dummy deepface module into sys.modules so that
    ``face_recognision_service`` can be imported without the real dependency.
    It also patches ``cv2.VideoCapture`` to avoid accessing real hardware.
    Each test receives the reloaded module instance.
    """
    # install dummy deepface to allow face_recognision_service import
    monkeypatch.setitem(
        sys.modules, "deepface", types.SimpleNamespace(DeepFace=DummyDeepFace())
    )
    # patch cv2.VideoCapture to return our DummyCap
    import cv2 as _cv2  # import cv2 to get the existing module reference

    monkeypatch.setattr(_cv2, "VideoCapture", lambda idx: DummyCap())
    # reload the service so it picks up our patches
    module = importlib.reload(
        importlib.import_module("backend.services.video_capture_service")
    )
    return module


def test_get_reference_prefers_explicit_path(video_module):
    """_get_reference should return a path tuple when expected_image_path is set."""
    camera = video_module.CameraInput(expected_image_path="/some/path.jpg")
    assert camera._get_reference() == ("path", "/some/path.jpg")


def test_get_reference_uses_embedding_when_provided(video_module):
    """_get_reference should retrieve an embedding when a hash and storage service are provided."""

    class DummyStorage:
        def __init__(self):
            self.called_with = []

        def get_embedding_by_hash(self, h):
            self.called_with.append(h)
            return [0.1, 0.2, 0.3]

    storage = DummyStorage()
    camera = video_module.CameraInput(
        image_storage_service=storage,
        expected_image_hash="abc123",
        expected_image_path=None,
    )
    assert camera._get_reference() == ("embedding", [0.1, 0.2, 0.3])
    assert storage.called_with == ["abc123"]


def test_get_reference_falls_back_to_bytes(video_module):
    """If no embedding is available, _get_reference should fall back to returning bytes."""

    class DummyStorage:
        def __init__(self):
            self.calls = []

        def get_embedding_by_hash(self, h):
            self.calls.append(("embed", h))
            return None

        def get_image_bytes_by_hash(self, h):
            self.calls.append(("bytes", h))
            return (b"data", "image/jpeg")

    storage = DummyStorage()
    camera = video_module.CameraInput(
        image_storage_service=storage,
        expected_image_hash="abc123",
        expected_image_path=None,
    )
    assert camera._get_reference() == ("bytes", (b"data", "image/jpeg"))
    assert ("embed", "abc123") in storage.calls and ("bytes", "abc123") in storage.calls


def test_get_reference_returns_none_when_no_data(video_module):
    """_get_reference should return None when nothing is configured."""

    class DummyStorage:
        def get_embedding_by_hash(self, h):
            return None

        def get_image_bytes_by_hash(self, h):
            return None

    storage = DummyStorage()
    camera = video_module.CameraInput(
        image_storage_service=storage, expected_image_hash="hash"
    )
    assert camera._get_reference() is None


def test_verify_face_after_qr_returns_true_for_path(video_module):
    """_verify_face_after_qr should return True when verify_face succeeds on a path reference."""
    cam = video_module.CameraInput(verification_timeout=1)
    # replace cap with a dummy that yields at least one frame
    cam.cap = DummyCap(reads=3)
    # replace face_service with one that returns True
    cam.face_service = DummyFaceService(result=True)
    result = cam._verify_face_after_qr(("path", "/ref.jpg"))
    assert result is True
    # ensure verify_face was called at least once
    assert cam.face_service.called_with


def test_verify_face_after_qr_returns_false_when_timeout(video_module):
    """_verify_face_after_qr should return False when verification never succeeds."""
    cam = video_module.CameraInput(verification_timeout=0)  # zero timeout prevents loop
    cam.cap = DummyCap(reads=1)
    cam.face_service = DummyFaceService(result=False)
    # using bytes ref should call verify_face_with_bytes or none due to timeout
    result = cam._verify_face_after_qr(("bytes", (b"data", "mime")))
    assert result is False
    # verify that no verification calls were made because loop did not run
    assert cam.face_service.called_with == []


def test_verify_face_after_qr_uses_embedding(video_module):
    """_verify_face_after_qr should call verify_face_with_embedding when given an embedding."""
    cam = video_module.CameraInput(verification_timeout=1)
    cam.cap = DummyCap(reads=1)
    cam.face_service = DummyFaceService(result=True)
    ref = ("embedding", [0.4, 0.4])
    result = cam._verify_face_after_qr(ref)
    assert result is True
    # ensure verify_face_with_embedding was invoked
    assert any(call[0] == "embedding" for call in cam.face_service.called_with)
