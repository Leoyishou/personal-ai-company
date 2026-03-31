#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Supabase Storage Client using direct REST API."""

import base64
import os
import uuid
import mimetypes
from pathlib import Path
from typing import Optional

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    # Try skill directory first
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path, override=False)
    # Also try project root
    project_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))
    if os.path.exists(project_root_env):
        load_dotenv(project_root_env, override=False)


def get_config():
    """Get Supabase configuration from environment."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    bucket = os.getenv("SUPABASE_BUCKET", "uploads")

    if not url:
        raise ValueError("Missing SUPABASE_URL environment variable")
    if not key:
        raise ValueError("Missing SUPABASE_KEY environment variable")

    # Ensure URL doesn't have trailing slash
    url = url.rstrip("/")

    return url, key, bucket


def upload_file(
    file_path: str,
    folder: str = "",
    filename: Optional[str] = None,
) -> str:
    """
    Upload a local file to Supabase Storage.

    Args:
        file_path: Local file path to upload
        folder: Optional folder path in the bucket
        filename: Optional custom filename, auto-generated if not provided

    Returns:
        Public URL of the uploaded file
    """
    url, key, bucket = get_config()

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Generate filename if not provided
    if not filename:
        ext = file_path.suffix or ".bin"
        filename = f"{uuid.uuid4().hex}{ext}"

    # Build storage path
    storage_path = f"{folder}/{filename}" if folder else filename
    storage_path = storage_path.lstrip("/")

    # Detect content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        content_type = "application/octet-stream"

    # Read file
    with open(file_path, "rb") as f:
        file_data = f.read()

    # Upload via REST API
    upload_url = f"{url}/storage/v1/object/{bucket}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": content_type,
        "x-upsert": "true",  # Overwrite if exists
    }

    response = requests.post(upload_url, headers=headers, data=file_data, timeout=60)

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Upload failed: {response.status_code} - {response.text}")

    # Build public URL
    public_url = f"{url}/storage/v1/object/public/{bucket}/{storage_path}"

    return public_url


def upload_base64(
    data: str,
    filename: Optional[str] = None,
    folder: str = "",
    content_type: str = "image/png",
) -> str:
    """
    Upload Base64 encoded data to Supabase Storage.

    Args:
        data: Base64 encoded data
        filename: Optional custom filename
        folder: Optional folder path in the bucket
        content_type: MIME type of the data

    Returns:
        Public URL of the uploaded file
    """
    url, key, bucket = get_config()

    # Generate filename if not provided
    if not filename:
        ext = mimetypes.guess_extension(content_type) or ".bin"
        filename = f"{uuid.uuid4().hex}{ext}"

    # Build storage path
    storage_path = f"{folder}/{filename}" if folder else filename
    storage_path = storage_path.lstrip("/")

    # Decode Base64
    file_data = base64.b64decode(data)

    # Upload via REST API
    upload_url = f"{url}/storage/v1/object/{bucket}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }

    response = requests.post(upload_url, headers=headers, data=file_data, timeout=60)

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Upload failed: {response.status_code} - {response.text}")

    # Build public URL
    public_url = f"{url}/storage/v1/object/public/{bucket}/{storage_path}"

    return public_url


def delete_file(storage_path: str) -> bool:
    """
    Delete a file from Supabase Storage.

    Args:
        storage_path: Path of the file in the bucket

    Returns:
        True if deleted successfully
    """
    url, key, bucket = get_config()

    delete_url = f"{url}/storage/v1/object/{bucket}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    response = requests.delete(
        delete_url,
        headers=headers,
        json={"prefixes": [storage_path]},
        timeout=30
    )

    if response.status_code not in (200, 204):
        raise RuntimeError(f"Delete failed: {response.status_code} - {response.text}")

    return True


def list_files(folder: str = "") -> list:
    """
    List files in a folder.

    Args:
        folder: Folder path in the bucket

    Returns:
        List of file objects
    """
    url, key, bucket = get_config()

    list_url = f"{url}/storage/v1/object/list/{bucket}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    body = {"prefix": folder, "limit": 100, "offset": 0}

    response = requests.post(list_url, headers=headers, json=body, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"List failed: {response.status_code} - {response.text}")

    return response.json()
