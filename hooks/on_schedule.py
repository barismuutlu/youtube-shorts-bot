"""
on_schedule.py — config.yaml'daki SCHEDULE_TIME ve SCHEDULE_DAYS'e göre
topics.txt'ten sıradaki konuyu alıp pipeline'ı çalıştırır.
Bağımlılık: pip install APScheduler
"""

import os
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
TOPICS_FILE = BASE_DIR / "input" / "topics.txt"

sys.path.insert(0, str(BASE_DIR))


def get_next_topic() -> str | None:
    """topics.txt'ten # ile işaretlenmemiş ilk konuyu döndür, sonra işaretle."""
    if not TOPICS_FILE.exists():
        logger.warning("topics.txt bulunamadı")
        return None

    lines = TOPICS_FILE.read_text(encoding="utf-8").splitlines()
    new_lines = []
    topic = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if topic is None:
            topic = stripped
            new_lines.append(f"# [DONE] {stripped}")
        else:
            new_lines.append(line)

    TOPICS_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return topic


def scheduled_job():
    topic = get_next_topic()
    if not topic:
        logger.warning("İşlenecek konu kalmadı, topics.txt'i güncelle")
        return

    logger.info(f"Zamanlı görev başladı: '{topic}'")
    try:
        from main import run_pipeline
        run_pipeline(source_type="topic", content=topic)
    except Exception as e:
        logger.error(f"Zamanlı pipeline hatası: {e}")


def start_scheduler():
    schedule_time = os.environ.get("SCHEDULE_TIME", "09:00")
    schedule_days = os.environ.get("SCHEDULE_DAYS", "mon,wed,fri")

    hour, minute = schedule_time.split(":")
    day_of_week = schedule_days

    scheduler = BlockingScheduler(timezone="Europe/Istanbul")
    scheduler.add_job(
        scheduled_job,
        trigger="cron",
        day_of_week=day_of_week,
        hour=int(hour),
        minute=int(minute),
    )

    logger.info(f"Zamanlayıcı başladı: her {day_of_week} saat {schedule_time}")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Zamanlayıcı durduruldu")


if __name__ == "__main__":
    # Hemen bir kez çalıştır (test için)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="Hemen bir kez çalıştır")
    args = parser.parse_args()

    if args.now:
        scheduled_job()
    else:
        start_scheduler()
