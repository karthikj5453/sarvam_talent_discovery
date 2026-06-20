import pytest
from unittest.mock import MagicMock
import boto3
from services.storage.s3_client import upload_file, get_presigned_url, download_file

@pytest.fixture(autouse=True)
def reset_s3_singleton(monkeypatch):
    import services.storage.s3_client as s3_client
    monkeypatch.setattr(s3_client, "_s3_client", None)

def test_upload_file_mock(monkeypatch):
    mock_s3 = MagicMock()
    mock_client = MagicMock(return_value=mock_s3)
    monkeypatch.setattr(boto3, "client", mock_client)
    monkeypatch.setattr("services.storage.s3_client._use_local", lambda: False)
    
    key = upload_file(b"testcontent", "testfolder", "testfile.txt")
    assert key == "testfolder/testfile.txt"
    mock_s3.put_object.assert_called_once_with(
        Bucket="sarvam-talent-audio",
        Key="testfolder/testfile.txt",
        Body=b"testcontent",
        ContentType="application/octet-stream"
    )

def test_get_presigned_url_mock(monkeypatch):
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://mock-s3-url.com/key"
    mock_client = MagicMock(return_value=mock_s3)
    monkeypatch.setattr(boto3, "client", mock_client)
    monkeypatch.setattr("services.storage.s3_client._use_local", lambda: False)
    
    url = get_presigned_url("testkey")
    assert url == "https://mock-s3-url.com/key"
    mock_s3.generate_presigned_url.assert_called_once()
