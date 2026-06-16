import pytest
import httpx
from services.sarvam.sarvam_client import transcribe_audio, text_to_speech, translate_text

@pytest.mark.anyio
async def test_translate_text_mock(monkeypatch):
    async def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"translated_text": "Hello, how are you?"}
        return MockResponse()
    
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    res = await translate_text("नमस्ते, आप कैसे हैं?", "hi-IN", "en-IN")
    assert res == "Hello, how are you?"

@pytest.mark.anyio
async def test_text_to_speech_mock(monkeypatch):
    async def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                # base64 for 'hello' is aGVsbG8=
                return {"audios": ["aGVsbG8="]}
        return MockResponse()
        
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    res = await text_to_speech("hello", "en-IN")
    assert res == b"hello"
