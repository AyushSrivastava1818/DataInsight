"""
StorageService — Dual-mode file storage abstraction.

When SUPABASE_URL + a Supabase storage key are set in the environment:
  - CSV files are uploaded to Supabase Storage (cloud bucket).
  - `filepath` saved in the DB is the Supabase storage object path (e.g. "csv/dataset_3_v2.csv").
  - Downloads are served via signed Supabase URLs (1-hour expiry).

When Supabase is NOT configured (local dev / SQLite mode):
  - Files are written to the local `storage/` directory.
  - `filepath` is a full OS path (e.g. "/app/storage/dataset_3_v2.csv").
  - Downloads are served directly from disk via FileResponse.

This abstraction means routers never need to know which storage backend is active.
"""

import os
import io
import logging
from typing import Optional, Tuple
import pandas as pd

from app.config import (
    STORAGE_DIR,
    SUPABASE_URL,
    SUPABASE_STORAGE_KEY,
    SUPABASE_BUCKET,
    USE_CLOUD_STORAGE,
)

logger = logging.getLogger(__name__)

# Initialize Supabase client lazily only when configured
_supabase = None
if USE_CLOUD_STORAGE:
    try:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_STORAGE_KEY)
        logger.info("[Storage] Supabase Storage client initialized.")
    except Exception as e:
        logger.error(f"[Storage] Failed to initialize Supabase client: {e}")


class StorageService:

    @staticmethod
    def save_dataframe(df: pd.DataFrame, filename: str) -> Tuple[str, int]:
        """
        Save a Pandas DataFrame as a CSV to either Supabase Storage or local disk.

        Args:
            df: The DataFrame to persist.
            filename: Target filename (e.g. "dataset_3_v2.csv").

        Returns:
            (filepath, file_size_bytes) — filepath is the storage path/key.
        """
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        file_size = len(csv_bytes)

        if USE_CLOUD_STORAGE and _supabase:
            try:
                return StorageService._upload_to_supabase(csv_bytes, filename), file_size
            except Exception as e:
                logger.error(f"[Storage] Supabase upload failed, falling back to local: {e}")
                return StorageService._save_locally(csv_bytes, filename), file_size
        else:
            return StorageService._save_locally(csv_bytes, filename), file_size

    @staticmethod
    def _upload_to_supabase(csv_bytes: bytes, filename: str) -> str:
        """Upload raw CSV bytes to Supabase Storage. Returns the object path."""
        object_path = f"csv/{filename}"
        try:
            # upsert=True overwrites the object if it already exists (safe for re-runs)
            _supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=object_path,
                file=csv_bytes,
                file_options={"content-type": "text/csv", "upsert": "true"},
            )
            logger.info(f"[Storage] Uploaded to Supabase: {object_path}")
            return object_path
        except Exception as e:
            logger.error(f"[Storage] Supabase upload failed: {e}")
            raise RuntimeError(f"Cloud storage upload failed: {e}")

    @staticmethod
    def _save_locally(csv_bytes: bytes, filename: str) -> str:
        """Write CSV bytes to the local storage directory. Returns the full OS path."""
        dest_path = os.path.join(STORAGE_DIR, filename)
        with open(dest_path, "wb") as f:
            f.write(csv_bytes)
        logger.info(f"[Storage] Saved locally: {dest_path}")
        return dest_path

    @staticmethod
    def read_csv_robustly(source) -> pd.DataFrame:
        """
        Reads a CSV from a file path (str), bytes, or file-like object robustly.
        Handles encoding issues (UTF-8, Latin-1, CP1252, UTF-16, UTF-8-sig) and
        auto-detects delimiters (comma, semicolon, tab, pipe).
        """
        import io
        import os

        # 1. Obtain raw bytes
        if isinstance(source, (str, os.PathLike)):
            try:
                with open(source, "rb") as f:
                    raw_bytes = f.read()
            except Exception:
                # Fallback to standard pandas read if file open fails
                return pd.read_csv(source)
        elif isinstance(source, bytes):
            raw_bytes = source
        elif hasattr(source, "read"):
            try:
                raw_bytes = source.read()
                if isinstance(raw_bytes, str):
                    raw_bytes = raw_bytes.encode("utf-8")
            except Exception:
                return pd.read_csv(source)
        else:
            return pd.read_csv(source)

        # 2. Decode text using multiple encodings
        decoded_text = None
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"]
        for encoding in encodings:
            try:
                decoded_text = raw_bytes.decode(encoding)
                break
            except Exception:
                continue

        if decoded_text is None:
            # Fallback to pandas default if all fail
            if isinstance(source, (str, os.PathLike)):
                return pd.read_csv(source)
            else:
                return pd.read_csv(io.BytesIO(raw_bytes))

        # 3. Detect delimiter on first line
        first_line = ""
        lines = decoded_text.splitlines()
        if lines:
            first_line = lines[0]

        delimiters = [',', ';', '\t', '|']
        counts = {d: first_line.count(d) for d in delimiters}
        best_delim = max(counts, key=counts.get)
        delimiter = best_delim if counts[best_delim] > 0 else ','

        # 4. Parse using pd.read_csv from StringIO
        return pd.read_csv(io.StringIO(decoded_text), sep=delimiter)

    @staticmethod
    def load_dataframe(filepath: str) -> pd.DataFrame:
        """
        Load a DataFrame from either a local path or a Supabase object path.
        Detects the source automatically by checking if filepath starts with "csv/".
        """
        if filepath.startswith("csv/") and USE_CLOUD_STORAGE and _supabase:
            try:
                return StorageService._download_from_supabase(filepath)
            except Exception as e:
                logger.error(f"[Storage] Supabase download failed, checking local backup: {e}")
                filename = os.path.basename(filepath)
                local_path = os.path.join(STORAGE_DIR, filename)
                if os.path.exists(local_path):
                    logger.info(f"[Storage] Found local backup copy: {local_path}")
                    return StorageService.read_csv_robustly(local_path)
                raise RuntimeError(f"Cloud storage download failed and no local backup copy found: {e}")
        else:
            return StorageService.read_csv_robustly(filepath)

    @staticmethod
    def _download_from_supabase(object_path: str) -> pd.DataFrame:
        """Download a CSV from Supabase Storage and return as a DataFrame."""
        try:
            response = _supabase.storage.from_(SUPABASE_BUCKET).download(object_path)
            return StorageService.read_csv_robustly(response)
        except Exception as e:
            logger.error(f"[Storage] Failed to download from Supabase: {e}")
            raise RuntimeError(f"Cloud storage download failed: {e}")

    @staticmethod
    def get_download_url(filepath: str, expiry_seconds: int = 3600) -> Optional[str]:
        """
        Returns a time-limited signed download URL for Supabase objects.
        Returns None for local-mode filepaths (routes serve these via FileResponse).
        """
        if filepath.startswith("csv/") and USE_CLOUD_STORAGE and _supabase:
            try:
                result = _supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                    filepath, expiry_seconds
                )
                return result.get("signedURL")
            except Exception as e:
                logger.error(f"[Storage] Failed to generate signed URL: {e}")
                return None
        return None

    @staticmethod
    def delete_file(filepath: str) -> None:
        """Delete a file from Supabase or local disk."""
        if filepath.startswith("csv/") and USE_CLOUD_STORAGE and _supabase:
            try:
                _supabase.storage.from_(SUPABASE_BUCKET).remove([filepath])
                logger.info(f"[Storage] Deleted from Supabase: {filepath}")
            except Exception as e:
                logger.warning(f"[Storage] Could not delete Supabase object: {e}")
        else:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.info(f"[Storage] Deleted locally: {filepath}")
                except Exception as e:
                    logger.warning(f"[Storage] Could not delete local file: {e}")
