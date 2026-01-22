import importlib
from typing import Optional, Tuple

import numpy as np
import pytest


class DummyDetector:
    """A simple dummy QRCode detector used to stub out cv2.QRCodeDetector."""

    def __init__(self, *, single_result: Optional[Tuple[str, object, object]] = None,
                 multi_result: Optional[Tuple[bool, list, object, object]] = None) -> None:
        self.single_result = single_result or ("", None, None)
        self.multi_result = multi_result or (False, [], None, None)

    # mimic the single decode API
    def detectAndDecode(self, frame):  # noqa: N802 (method name matches OpenCV API)
        return self.single_result

    # mimic the multi decode API
    def detectAndDecodeMulti(self, frame):  # noqa: N802
        return self.multi_result


def test_detect_qr_single_returns_text(monkeypatch):
    """detect_qr should return decoded text when present in single mode."""
    module = importlib.import_module("backend.services.qr_service")
    detector = module.CodeDetector(multi_mode=False)
    # patch the underlying detector to return a known result
    dummy = DummyDetector(single_result=("hello", None, None))
    monkeypatch.setattr(detector, "detector", dummy)
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    assert detector.detect_qr(frame) == "hello"


def test_detect_qr_single_returns_none_when_no_text(monkeypatch):
    """detect_qr should return None when no code is found."""
    module = importlib.import_module("backend.services.qr_service")
    detector = module.CodeDetector(multi_mode=False)
    dummy = DummyDetector(single_result=("", None, None))
    monkeypatch.setattr(detector, "detector", dummy)
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    assert detector.detect_qr(frame) is None


def test_detect_qr_multi_returns_first_valid_text(monkeypatch):
    """In multi mode the first non‑empty decoded string should be returned."""
    module = importlib.import_module("backend.services.qr_service")
    detector = module.CodeDetector(multi_mode=True)
    dummy = DummyDetector(multi_result=(True, ["", "abc", "xyz"], None, None))
    monkeypatch.setattr(detector, "detector", dummy)
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    assert detector.detect_qr(frame) == "abc"


def test_detect_qr_multi_returns_none_when_no_codes(monkeypatch):
    """When multi detection finds nothing, detect_qr should return None."""
    module = importlib.import_module("backend.services.qr_service")
    detector = module.CodeDetector(multi_mode=True)
    dummy = DummyDetector(multi_result=(False, [], None, None))
    monkeypatch.setattr(detector, "detector", dummy)
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    assert detector.detect_qr(frame) is None


def test_detect_qr_with_points_returns_text_and_points(monkeypatch):
    """detect_qr_with_points should return both the decoded text and corner points."""
    module = importlib.import_module("backend.services.qr_service")
    detector = module.CodeDetector(multi_mode=False)
    # prepare a dummy result containing text and a placeholder points array
    dummy = DummyDetector(single_result=("data", "points", None))
    monkeypatch.setattr(detector, "detector", dummy)
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    text, points = detector.detect_qr_with_points(frame)
    assert text == "data"
    assert points == "points"


def test_decode_qr_from_bytes_returns_decoded_text(monkeypatch):
    """decode_qr_from_bytes should decode the image and return the decoded QR text."""
    module = importlib.import_module("backend.services.qr_service")
    # patch np.frombuffer to return a numpy array
    monkeypatch.setattr(module.np, "frombuffer", lambda b, dtype: np.array([1, 2, 3], dtype=np.uint8))
    # patch cv2.imdecode to return a dummy image array
    monkeypatch.setattr(module.cv, "imdecode", lambda arr, flags: np.zeros((10, 10, 3), dtype=np.uint8))
    # patch CodeDetector.detect_qr to return a known string
    monkeypatch.setattr(module.CodeDetector, "detect_qr", lambda self, img: "decoded")
    result = module.decode_qr_from_bytes(b"image bytes")
    assert result == "decoded"


def test_decode_qr_from_bytes_handles_decode_failure(monkeypatch):
    """decode_qr_from_bytes should return None if the image cannot be decoded."""
    module = importlib.import_module("backend.services.qr_service")
    # patch cv2.imdecode to return None, simulating a decode error
    monkeypatch.setattr(module.cv, "imdecode", lambda arr, flags: None)
    result = module.decode_qr_from_bytes(b"invalid image")
    assert result is None