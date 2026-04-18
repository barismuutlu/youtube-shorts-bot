"""
Video Renderer — Script JSON'ı Remotion CLI'ya geçirerek video render eder.
Girdi: TTS ile güncellenmiş script JSON, session ID
Çıktı: output/videos/{session_id}.mp4
"""

import json
import math
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
OUTPUT_VIDEOS_DIR = BASE_DIR / "output" / "videos"
OUTPUT_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
REMOTION_DIR = BASE_DIR / "remotion"

FPS = 30


def prepare_props(script: dict, session_id: str) -> dict:
    """Script'e frame bilgilerini ekle, Remotion props JSON'ını hazırla."""
    lines = []
    cumulative_frames = 0

    footage_dir = REMOTION_DIR / "public" / "footage"
    footage_files = list(footage_dir.glob("*.mp4"))
    footage_file = footage_files[0].name if footage_files else "parkour_001.mp4"

    for line in script["lines"]:
        updated = dict(line)
        # ceil() ile ses dosyası sonunda kesilmez; tam sayı birikimi ile float kayması olmaz
        duration_frames = math.ceil(line["duration"] * FPS)
        updated["startFrame"] = cumulative_frames
        updated["durationFrames"] = duration_frames
        cumulative_frames += duration_frames
        lines.append(updated)

    total_duration_sec = cumulative_frames / FPS

    return {
        "sessionId": session_id,
        "lines": lines,
        "totalDurationSec": total_duration_sec,
        "footageFile": footage_file,
    }


def render_video(script: dict, session_id: str, output_path: Path = None, topic_slug: str = None) -> Path:
    if output_path is None:
        name = topic_slug or session_id
        output_path = OUTPUT_VIDEOS_DIR / f"{name}.mp4"

    props = prepare_props(script, session_id)
    total_frames = math.ceil(props["totalDurationSec"] * FPS)

    props_file = Path(f"/tmp/{session_id}_props.json")
    with open(props_file, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False)

    logger.info(f"Remotion render başlıyor: {total_frames} frame ({props['totalDurationSec']:.1f}sn)")
    logger.info(f"Çıktı: {output_path}")

    cmd = [
        "npx", "remotion", "render",
        "src/index.ts",
        "ShortVideo",
        str(output_path.resolve()),
        "--props", str(props_file.resolve()),
        "--codec", "h264",
        "--height", "1920",
        "--width", "1080",
        "--fps", str(FPS),
        "--log", "verbose",
    ]

    logger.debug(f"Komut: {' '.join(cmd)}")

    subprocess.run(
        cmd,
        cwd=str(REMOTION_DIR),
        check=True,
        text=True,
        capture_output=False,
    )

    props_file.unlink(missing_ok=True)

    if not output_path.exists():
        raise FileNotFoundError(f"Render tamamlandı ama çıktı bulunamadı: {output_path}")

    size_mb = output_path.stat().st_size / 1024 / 1024
    logger.success(f"Video render tamamlandı: {output_path} ({size_mb:.1f} MB)")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remotion ile video render")
    parser.add_argument("--script", required=True, help="TTS güncellenmiş script JSON yolu")
    parser.add_argument("--session", type=str, help="Session ID (opsiyonel)")
    parser.add_argument("--output", type=str, help="Çıktı MP4 yolu (opsiyonel)")
    args = parser.parse_args()

    with open(args.script, encoding="utf-8") as f:
        script_data = json.load(f)

    session_id = args.session or script_data.get("session_id") or datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.output) if args.output else None

    video_path = render_video(script_data, session_id, out_path)
    print(f"\nVideo hazır: {video_path}")
