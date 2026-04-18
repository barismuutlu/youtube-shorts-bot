"""
Drive Uploader — Google Drive'a video yükleme.
Service Account JSON kullanır — tarayıcı açmaz, OAuth gerektirmez.

Kurulum:
  1. Google Cloud Console → IAM & Admin → Service Accounts → Create
  2. JSON key indir → service_account.json olarak proje köküne kaydet
  3. Drive klasörünü service account e-postasıyla paylaş (Editor yetkisi)
"""

import os
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

SERVICE_ACCOUNT_FILE = Path(__file__).parent.parent / "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _get_service():
    from googleapiclient.discovery import build
    from google.oauth2 import service_account

    if not SERVICE_ACCOUNT_FILE.exists():
        raise FileNotFoundError(
            f"service_account.json bulunamadı: {SERVICE_ACCOUNT_FILE}\n"
            "Google Cloud Console → IAM & Admin → Service Accounts → Create → Keys → Add Key → JSON\n"
            "İndirilen dosyayı service_account.json olarak proje köküne kaydet."
        )

    creds = service_account.Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_FILE), scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def upload_to_drive(
    video_path: str,
    folder_id: str = None,
    filename: str = None,
) -> dict:
    """
    Videoyu Google Drive'a yükle.
    Dönüş: {"file_id": "...", "web_link": "...", "name": "..."}
    """
    from googleapiclient.http import MediaFileUpload

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video bulunamadı: {video_path}")

    folder_id = folder_id or os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        raise EnvironmentError("GOOGLE_DRIVE_FOLDER_ID .env'de tanımlı değil")

    if filename is None:
        filename = video_path.name

    service = _get_service()

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,
    )

    size_mb = video_path.stat().st_size / 1024 / 1024
    logger.info(f"Drive'a yükleniyor: {filename} ({size_mb:.1f} MB)")

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
