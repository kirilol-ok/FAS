import importlib
import sys
import types
from io import BytesIO

import pytest

# The email_service module depends on external packages (qrcode, fastapi and fastapi_mail)
# that may not be available in the test environment.  To make the module
# importable for testing we insert dummy implementations into sys.modules
# before importing it.  These dummies mimic just enough of the original
# APIs for the service functions to operate without raising errors.


class DummyQRCodeImage:
    """Minimal image object used by DummyQRCode to write bytes to a buffer."""

    def __init__(self, output_bytes: bytes) -> None:
        self._output_bytes = output_bytes

    def save(self, buf: BytesIO, format: str = "PNG") -> None:
        # write predetermined PNG bytes into the provided buffer
        buf.write(self._output_bytes)


class DummyQRCode:
    """
    Simplified stand-in for qrcode.QRCode.  This dummy stores the data passed
    to ``add_data`` and returns an object whose ``save`` method writes a fixed
    byte sequence to the given buffer.
    """

    def __init__(self, *args, **kwargs) -> None:
        self.data = None

    def add_data(self, data: str) -> None:
        self.data = data

    def make(self, fit: bool = True) -> None:
        # no operation needed for dummy
        return None

    def make_image(
        self, fill_color: str = "black", back_color: str = "white"
    ) -> DummyQRCodeImage:
        # return an object capable of writing bytes to a file-like buffer
        return DummyQRCodeImage(b"FAKEPNG")


class DummyFastMail:
    """Records calls to ``send_message`` for verification in tests."""

    def __init__(self, conf: object) -> None:
        # accept any configuration object
        self.conf = conf
        self.sent_message = None

    async def send_message(self, message: object) -> None:
        # record the sent message so the test can assert on it later
        self.sent_message = message


class DummyMessageSchema:
    """Captures initialization arguments to mirror fastapi_mail.MessageSchema."""

    def __init__(self, **kwargs) -> None:
        # store the provided keyword arguments for inspection
        self.kwargs = kwargs
        self.subject = kwargs.get("subject")
        self.recipients = kwargs.get("recipients")
        self.body = kwargs.get("body")
        self.subtype = kwargs.get("subtype")
        self.attachments = kwargs.get("attachments")


class DummyMessageType:
    """Provides a single attribute ``html`` used by email_service."""

    html = "html"


class DummyConnectionConfig:
    """Stub for fastapi_mail.ConnectionConfig."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyUploadFile:
    """Simple replacement for fastapi.UploadFile used in attachments."""

    def __init__(self, file: BytesIO, filename: str) -> None:
        self.file = file
        self.filename = filename


@pytest.fixture(autouse=True)
def email_module(monkeypatch):
    """
    Provide a freshly imported ``email_service`` module with required external
    dependencies patched.

    The email_service module is imported inside this fixture after installing
    dummy qrcode, fastapi_mail and fastapi modules into ``sys.modules``.  Each
    test receives the reloaded module instance.
    """
    # install dummy qrcode, fastapi_mail and fastapi modules before import
    dummy_qrcode = types.SimpleNamespace(
        QRCode=DummyQRCode,
        constants=types.SimpleNamespace(ERROR_CORRECT_L=1),
    )
    dummy_fastapi_mail = types.SimpleNamespace(
        ConnectionConfig=DummyConnectionConfig,
        FastMail=DummyFastMail,
        MessageSchema=DummyMessageSchema,
        MessageType=DummyMessageType,
    )
    dummy_fastapi = types.SimpleNamespace(
        UploadFile=DummyUploadFile,
    )
    monkeypatch.setitem(sys.modules, "qrcode", dummy_qrcode)
    monkeypatch.setitem(sys.modules, "fastapi_mail", dummy_fastapi_mail)
    monkeypatch.setitem(sys.modules, "fastapi", dummy_fastapi)
    # reload the module so it picks up the dummy modules
    email_mod = importlib.reload(
        importlib.import_module("backend.services.email_service")
    )
    return email_mod


def test_generate_qr_in_memory_returns_bytesio(email_module):
    """Ensure generate_qr_in_memory returns a BytesIO containing the PNG data."""
    result = email_module.generate_qr_in_memory("some data")
    # should be an in-memory binary stream
    assert isinstance(result, BytesIO)
    # the dummy QR generator writes ``b"FAKEPNG"``
    assert result.getvalue() == b"FAKEPNG"


@pytest.mark.asyncio
async def test_send_qr_code_email_invokes_send_message(email_module):
    """send_qr_code_email should create a message and pass it to FastMail.send_message."""
    # patch generate_qr_in_memory to return a known buffer
    dummy_buffer = BytesIO(b"PNGDATA")
    # monkeypatch the function on the imported module
    email_module.generate_qr_in_memory = lambda data: dummy_buffer

    # prepare to capture the sent message
    sent: dict = {}

    class CapturingFastMail(DummyFastMail):
        async def send_message(self, message: object) -> None:
            sent["message"] = message
            await super().send_message(message)

    # replace the FastMail class on the module with our capturing subclass
    email_module.FastMail = CapturingFastMail
    # call the async function
    await email_module.send_qr_code_email(
        email_to="user@example.com", qr_data="dummy", first_name="Tester"
    )
    # ensure send_message was invoked exactly once and the message recorded
    assert "message" in sent
    message = sent["message"]
    # verify minimal properties on the message created by DummyMessageSchema
    assert isinstance(message, DummyMessageSchema)
    assert message.recipients == ["user@example.com"]
    assert message.subject == "Twój Kod Dostępu QR"
