"""
Drive Uploader — Google Drive'a video yükleme.
Google Drive Python SDK (google-api-python-client) kullanır.
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def upload_to_drive(
    video_path: str,
    folder_id: str = None,
    filename: str = None,
) -> dict:
    """
    Videoyu Google Drive'a yükle.
    Dönüş: {"file_id": "...", "web_link": "...", "name": "..."}
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        raise ImportError(
            "Google Drive SDK eksik. Kur: pip install google-api-python-client google-auth"
        )

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video bulunamadı: {video_path}")

    folder_id = folder_id or os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        raise EnvironmentError("GOOGLE_DRIVE_FOLDER_ID .env'de tanımlı değil")

    if filename is None:
        filename = video_path.name

    # Service account credentials
    creds_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")

    creds = service_account.Credentials.from_service_account_file(
        creds_path,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )

    service = build("drive", "v3", credentials=creds)

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,  # 5MB chunk
    )

    logger.info(f"Drive'a yükleniyor: {filename} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")

    request = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink",
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.debug(f"  Yükleme: {int(status.progress() * 100)}%")

    result = {
        "file_id": response["id"],
        "name": response["name"],
        "web_link": response.get("webViewLink", ""),
    }

    logger.success(f"Drive'a yüklendi: {result['web_link']}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Drive'a video yükle")
    parser.add_argument("video", help="MP4 dosya yolu")
    parser.add_argument("--folder", type=str, help="Drive klasör ID (opsiyonel, .env'den okunur)")
    parser.add_argument("--name", type=str, help="Drive'daki dosya adı (opsiyonel)")
    args = parser.parse_args()

    result = upload_to_drive(args.video, args.folder, args.name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
