"""
S3 Storage Service
Handles upload/download of audio files and resumes.
Uses boto3 with presigned URLs for direct browser access.
"""
import io
import uuid
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Optional
from config import settings

# ─── S3 CLIENT ────────────────────────────────────────────────

def _get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        config=Config(signature_version="s3v4"),
    )


# ─── UPLOAD ───────────────────────────────────────────────────

def upload_file(
    file_bytes: bytes,
    folder: str,
    filename: Optional[str] = None,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload raw bytes to S3.

    Args:
        file_bytes:   Raw file content
        folder:       S3 prefix/folder (e.g. 'audio/intros', 'resumes')
        filename:     Override filename. Auto-generates UUID key if None.
        content_type: MIME type (e.g. 'audio/wav', 'application/pdf')

    Returns:
        str: Full S3 key (e.g. 'audio/intros/abc-123.wav')
    """
    s3 = _get_s3_client()
    key = f"{folder}/{filename or str(uuid.uuid4())}"

    s3.put_object(
        Bucket=settings.AWS_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return key


def upload_audio(audio_bytes: bytes, candidate_id: str, label: str = "audio") -> str:
    """
    Upload an audio file for a candidate. Returns the S3 key.
    label examples: 'intro', 'answer_0', 'answer_1', 'hr_summary'
    """
    filename = f"{candidate_id}_{label}.wav"
    return upload_file(
        audio_bytes,
        folder="audio",
        filename=filename,
        content_type="audio/wav",
    )


def upload_resume(pdf_bytes: bytes, candidate_id: str) -> str:
    """Upload a resume PDF. Returns the S3 key."""
    filename = f"{candidate_id}_resume.pdf"
    return upload_file(
        pdf_bytes,
        folder="resumes",
        filename=filename,
        content_type="application/pdf",
    )


# ─── PRESIGNED URL ────────────────────────────────────────────

def get_presigned_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    """
    Generate a time-limited presigned URL for direct browser access.

    Args:
        s3_key:         The S3 object key returned by upload_file()
        expiry_seconds: How long the URL stays valid (default: 1 hour)

    Returns:
        str: HTTPS presigned URL
    """
    s3 = _get_s3_client()
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
    return url


# ─── DOWNLOAD ─────────────────────────────────────────────────

def download_file(s3_key: str) -> bytes:
    """Download a file from S3 and return its raw bytes."""
    s3 = _get_s3_client()
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=s3_key)
    return response["Body"].read()


# ─── DELETE ───────────────────────────────────────────────────

def delete_file(s3_key: str) -> None:
    """Delete a file from S3."""
    s3 = _get_s3_client()
    s3.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=s3_key)


# ─── HELPER: S3 key → public URL ──────────────────────────────

def key_to_url(s3_key: str) -> str:
    """
    Convert an S3 key to a presigned URL (1 hour expiry by default).
    Use this anywhere you need to return a playable audio link.
    """
    return get_presigned_url(s3_key, expiry_seconds=3600)
