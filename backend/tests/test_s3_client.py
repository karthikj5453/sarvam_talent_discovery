import pytest
from unittest.mock import MagicMock
import boto3
from services.storage.s3_client import upload_file, get_presigned_url, download_file

def test_upload_file_mock(monkeypatch):
    mock_s3 = MagicMock()
    mock_client = MagicMock(return_value=mock_s3)
    monkeypatch.setattr(boto3, "client", mock_client)
    
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
    
    url = get_presigned_url("testkey")
    assert url == "https://mock-s3-url.com/key"
    mock_s3.generate_presigned_url.assert_called_once()
