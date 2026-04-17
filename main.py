"""
main.py — YouTube Shorts bot ana orkestrasyon pipeline.

Kullanım:
  python main.py --topic "Kara delikler nasıl çalışır"
  python main.py --pdf input/pdfs/makale.pdf
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# Log dosyası
LOG_FILE = OUTPUT_DIR / "logs" / f"run_{datetime.now().strftime('%Y%m%d')}.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logger.add(LOG_FILE, rotation="1 day", retention="7 days", encoding="utf-8")


def generate_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def run_pipeline(source_type: str, content: str) -> dict:
    """
    Tam pipeline:
      1. Script üret (Claude API)
      2. TTS seslendirme (ElevenLabs)
      3. Video render (Remotion)
      4. Kalite kontrol (ffprobe)
      5. Drive'a yükle
      6. Tamamlama bildirimi
    """
    session_id = generate_session_id()
    logger.info(f"Pipeline başladı: session={session_id}, kaynak={source_type}")

    # ── 1. Script üretimi ──────────────────────────────────────────────
    from skills.script_generator import generate_script, save_script

    if source_type == "topic":
        script = generate_script(topic=content)
    elif source_type == "pdf":
        script = generate_script(pdf_path=content)
    else:
        raise ValueError(f"Bilinmeyen source_type: {source_type}")

    save_script(script, session_id)
    logger.info(f"[1/6] Script hazır: {script['title']} ({script['total_duration']:.1f}sn)")

    # ── 2. TTS seslendirme ─────────────────────────────────────────────
    from skills.tts_engine import run_tts

    script = run_tts(script, session_id)
    logger.info(f"[2/6] TTS tamamlandı: {len(script['lines'])} replik")

    # Güncellenmiş scripti kaydet
    script_path = OUTPUT_DIR / "scripts" / f"{session_id}_tts.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    # ── 3. Video render ────────────────────────────────────────────────
    from skills.video_renderer import render_video

    video_path = render_video(script, session_id)
    logger.info(f"[3/6] Video render tamamlandı: {video_path}")

    # ── 4. Kalite kontrol ──────────────────────────────────────────────
    from skills.quality_checker import check_video

    quality = check_video(str(video_path))
    logger.info(f"[4/6] Kalite kontrol geçti: {quality['duration']}sn, {quality['resolution']}")

    # ── 5. Drive yükleme ───────────────────────────────────────────────
    from skills.drive_uploader import upload_to_drive

    date_str = datetime.now().strftime("%Y%m%d")
    topic_slug = script["title"].lower().replace(" ", "_")[:30]
    drive_filename = f"{date_str}_{topic_slug}_{session_id[-6:]}.mp4"

    drive_result = upload_to_drive(str(video_path), filename=drive_filename)
    logger.info(f"[5/6] Drive yüklendi: {drive_result['web_link']}")

    # ── 6. Tamamlama bildirimi ─────────────────────────────────────────
    from hooks.on_complete import notify

    summary = notify(session_id, drive_result, script)
    logger.success(f"[6/6] Pipeline tamamlandı: {session_id}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Shorts bot")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic", type=str, help="Konu metni")
    group.add_argument("--pdf", type=str, help="PDF dosya yolu")
    args = parser.parse_args()

    if args.topic:
        result = run_pipeline("topic", args.topic)
    else:
        result = run_pipeline("pdf", args.pdf)

    print(json.dumps(result, ensure_ascii=False, indent=2))
