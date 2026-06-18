"""
S3 Storage Service — with local disk fallback for dev
Handles upload/download of audio files and resumes.

In development (when AWS creds are absent/placeholder):
  - Files are stored under LOCAL_STORAGE_PATH on disk
  - URLs are served via FastAPI StaticFiles at /static/audio

In production (when real AWS creds are set):
  - Files go to S3 with presigned URLs
"""
import io
import os
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Optional
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

# ─── HELPERS ──────────────────────────────────────────────────

def _use_local() -> bool:
    """Check whether to use local disk storage instead of S3."""
    return settings.use_local_storage()


def _local_base() -> Path:
    """Return the local storage directory, creating it if needed."""
    path = Path(settings.LOCAL_STORAGE_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


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
    Upload raw bytes to S3 or local disk.

    Args:
        file_bytes:   Raw file content
        folder:       S3 prefix / local subfolder (e.g. 'audio', 'resumes')
        filename:     Override filename. Auto-generates UUID key if None.
        content_type: MIME type (e.g. 'audio/wav', 'application/pdf')

    Returns:
        str: Key that can be passed to key_to_url() to get a playable URL.
             Local: relative path like 'audio/abc-123.wav'
             S3: full S3 key like 'audio/abc-123.wav'
    """
    fname = filename or str(uuid.uuid4())
    key = f"{folder}/{fname}"

    if _use_local():
        dest = _local_base() / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(file_bytes)
        logger.debug(f"[Storage] Saved locally: {dest}")
        return key

    # ── S3 path ───────────────────────────────────────────────
    s3 = _get_s3_client()
    s3.put_object(
        Bucket=settings.AWS_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    logger.debug(f"[Storage] Uploaded to S3: {key}")
    return key


def upload_audio(audio_bytes: bytes, candidate_id: str, label: str = "audio") -> str:
    """
    Upload an audio file for a candidate. Returns the storage key.
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
    """Upload a resume PDF. Returns the storage key."""
    filename = f"{candidate_id}_resume.pdf"
    return upload_file(
        pdf_bytes,
        folder="resumes",
        filename=filename,
        content_type="application/pdf",
    )


# ─── PRESIGNED URL / LOCAL URL ────────────────────────────────

def key_to_url(key: str, expiry_seconds: int = 3600) -> str:
    """
    Convert a storage key to a URL.
    Local mode: returns /static/audio/<key>
    S3 mode:    returns a presigned HTTPS URL
    """
    if _use_local():
        # StaticFiles is mounted at /static/audio → /static/audio/audio/file.wav
        return f"/static/audio/{key}"

    return get_presigned_url(key, expiry_seconds=expiry_seconds)


def get_presigned_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    """
    Generate a time-limited presigned URL for direct browser access (S3 only).
    """
    s3 = _get_s3_client()
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
    return url


# ─── DOWNLOAD ─────────────────────────────────────────────────

def download_file(key: str) -> bytes:
    """Download a file from S3 or local disk."""
    if _use_local():
        dest = _local_base() / key
        return dest.read_bytes()

    s3 = _get_s3_client()
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=key)
    return response["Body"].read()


# ─── DELETE ───────────────────────────────────────────────────

def delete_file(key: str) -> None:
    """Delete a file from S3 or local disk."""
    if _use_local():
        dest = _local_base() / key
        if dest.exists():
            dest.unlink()
        return

    s3 = _get_s3_client()
    s3.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=key)
