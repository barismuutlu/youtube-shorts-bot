"""
main.py — YouTube Shorts bot ana orkestrasyon pipeline.

Kullanım:
  python main.py --topic "Deadlocks and Banker Algorithm"
  python main.py --pdf input/pdfs/article.pdf
  python main.py --all-topics          # topics.txt'teki tüm konuları işle
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

LOG_FILE = OUTPUT_DIR / "logs" / f"run_{datetime.now().strftime('%Y%m%d')}.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logger.add(LOG_FILE, rotation="1 day", retention="7 days", encoding="utf-8")


def generate_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_topics() -> list[str]:
    topics_file = BASE_DIR / "input" / "topics.txt"
    lines = topics_file.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def run_pipeline(source_type: str, content: str) -> dict:
    """
    Full pipeline:
      1. Script generation (Claude API)
      2. TTS voiceover (ElevenLabs)
      3. Video render (Remotion)
      4. Quality check (ffprobe)
      5. Upload to Drive
      6. Completion notification
    """
    session_id = generate_session_id()
    logger.info(f"Pipeline started: session={session_id}, source={source_type}")

    # ── 1. Script generation ───────────────────────────────────────────
    from skills.script_generator import generate_script, save_script, save_seo_metadata

    if source_type == "topic":
        script = generate_script(topic=content)
    elif source_type == "pdf":
        script = generate_script(pdf_path=content)
    else:
        raise ValueError(f"Unknown source_type: {source_type}")

    topic_slug = script.get("topic_slug") or session_id
    save_script(script, session_id)
    save_seo_metadata(script, topic_slug)
    logger.info(f"[1/6] Script ready: {script['title']} ({script['total_duration']:.1f}s)")
    logger.info(f"      SEO title: {script.get('seo_title', 'N/A')}")

    # ── 2. TTS voiceover ───────────────────────────────────────────────
    from skills.tts_engine import run_tts

    script = run_tts(script, session_id)
    logger.info(f"[2/6] TTS done: {len(script['lines'])} lines")

    script_tts_path = OUTPUT_DIR / "scripts" / f"{session_id}_tts.json"
    with open(script_tts_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    # ── 3. Video render ────────────────────────────────────────────────
    from skills.video_renderer import render_video

    video_path = render_video(script, session_id, topic_slug=topic_slug)
    logger.info(f"[3/6] Video render done: {video_path}")

    # ── 4. Quality check ───────────────────────────────────────────────
    from skills.quality_checker import check_video

    quality = check_video(str(video_path))
    logger.info(f"[4/6] Quality check passed: {quality['duration']}s, {quality['resolution']}")

    # ── 5. Drive upload ────────────────────────────────────────────────
    from skills.drive_uploader import upload_to_drive

    drive_filename = f"{topic_slug}.mp4"
    drive_result = upload_to_drive(str(video_path), filename=drive_filename)
    logger.info(f"[5/6] Uploaded to Drive: {drive_result['web_link']}")

    # ── 6. Completion notification ─────────────────────────────────────
    from hooks.on_complete import notify

    summary = notify(session_id, drive_result, script)
    logger.success(f"[6/6] Pipeline complete: {session_id} → {topic_slug}.mp4")

    return summary


def run_all_topics() -> list[dict]:
    topics = read_topics()
    if not topics:
        logger.error("topics.txt is empty or not found")
        sys.exit(1)

    logger.info(f"Processing {len(topics)} topics from topics.txt")
    results = []

    for i, topic in enumerate(topics, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Topic {i}/{len(topics)}: {topic}")
        logger.info(f"{'='*60}")
        try:
            result = run_pipeline("topic", topic)
            results.append({"topic": topic, "status": "ok", **result})
        except Exception as e:
            logger.error(f"Failed for topic '{topic}': {e}")
            results.append({"topic": topic, "status": "error", "error": str(e)})

        # Brief pause between topics to avoid rate limits
        if i < len(topics):
            logger.info("Waiting 3s before next topic...")
            time.sleep(3)

    logger.success(f"\nAll topics done: {sum(1 for r in results if r['status'] == 'ok')}/{len(topics)} successful")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Shorts bot")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic", type=str, help="Single topic text")
    group.add_argument("--pdf", type=str, help="PDF file path")
    group.add_argument("--all-topics", action="store_true", help="Process all topics from input/topics.txt")
    args = parser.parse_args()

    if args.all_topics:
        results = run_all_topics()
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.topic:
        result = run_pipeline("topic", args.topic)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = run_pipeline("pdf", args.pdf)
        print(json.dumps(result, ensure_ascii=False, indent=2))
