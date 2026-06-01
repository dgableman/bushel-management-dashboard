"""
Read-side helper for fetching contract PDFs from a private Google Cloud
Storage bucket.

The desktop app uploads PDFs keyed by contract number (see the main project's
utils/contract_pdf_storage.py). Here we resolve the same object key and stream
the bytes back so the dashboard can offer a download button.

Credentials resolution order:
  1. st.secrets["gcp_service_account"]  (recommended for Streamlit Cloud)
  2. GOOGLE_APPLICATION_CREDENTIALS env / local service-account JSON file
  3. Ambient credentials
"""
import os
import re
from typing import Optional

import streamlit as st

BUCKET_NAME = os.environ.get("CONTRACT_PDF_BUCKET", "peerless-watch-474016-b6-contract-pdfs")
_BLOB_PREFIX = "contracts/"

# Local fallback credential path (same key used by the desktop app).
_LOCAL_CRED_PATH = "/home/dgableman/JSON/peerless-watch-474016-b6-d2167f90d3a2.json"


def blob_name_for_contract(contract_number: str) -> str:
    """Mirror the desktop uploader's object key derivation."""
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", (contract_number or "").strip())
    return f"{_BLOB_PREFIX}{safe}.pdf"


@st.cache_resource(show_spinner=False)
def _get_bucket():
    """Build a cached GCS bucket handle, or return None if unavailable."""
    try:
        from google.cloud import storage
    except Exception:
        return None

    client = None
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            client = storage.Client.from_service_account_info(info)
    except Exception:
        client = None

    if client is None:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not (cred_path and os.path.exists(cred_path)) and os.path.exists(_LOCAL_CRED_PATH):
            cred_path = _LOCAL_CRED_PATH
        try:
            if cred_path and os.path.exists(cred_path):
                client = storage.Client.from_service_account_json(cred_path)
            else:
                client = storage.Client()
        except Exception:
            return None

    try:
        return client.bucket(BUCKET_NAME)
    except Exception:
        return None


def storage_available() -> bool:
    """True if we have a usable bucket handle (credentials present)."""
    return _get_bucket() is not None


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_pdf_bytes(contract_number: str) -> Optional[bytes]:
    """Download a contract's PDF bytes from the bucket. None if missing."""
    bucket = _get_bucket()
    if bucket is None:
        return None
    blob = bucket.blob(blob_name_for_contract(contract_number))
    try:
        if not blob.exists():
            return None
        return blob.download_as_bytes()
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=600)
def list_available_contract_numbers():
    """Return the contract numbers that currently have a PDF in the bucket.

    One cached bucket listing, so callers can cheaply decide which rows get a
    link without an existence check per row.
    """
    bucket = _get_bucket()
    if bucket is None:
        return []
    try:
        names = set()
        for blob in bucket.list_blobs(prefix=_BLOB_PREFIX):
            n = blob.name[len(_BLOB_PREFIX):]
            if n.endswith(".pdf"):
                n = n[:-4]
            if n:
                names.add(n)
        return sorted(names)
    except Exception:
        return []


def signed_url_for_contract(contract_number: str, expiration_seconds: int = 7 * 24 * 3600) -> Optional[str]:
    """Generate a time-limited signed URL to view a contract's PDF inline.

    Signing happens locally with the service-account key (no network call).
    Callers should pass only contract numbers known to exist (see
    list_available_contract_numbers) so links never point at missing files.
    """
    from datetime import timedelta

    bucket = _get_bucket()
    if bucket is None:
        return None
    blob = bucket.blob(blob_name_for_contract(contract_number))
    try:
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration_seconds),
            method="GET",
            response_type="application/pdf",  # open inline in the browser
        )
    except Exception:
        return None
