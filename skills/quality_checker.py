"""
Quality Checker — ffprobe ile video doğrulama.
Süre, çözünürlük, ses seviyesi ve bütünlük kontrolleri.
"""

import json
import subprocess
import argparse
from pathlib import Path

from loguru import logger

MIN_DURATION = 25
MAX_DURATION = 60
EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1920


def probe_video(path: str) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def check_audio_loudness(path: str) -> float:
    """LUFS ölçümü (ffmpeg loudnorm filtresi ile)."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-i", path,
                "-af", "loudnorm=print_format=json",
                "-f", "null", "-",
            ],
            capture_output=True,
            text=True,
        )
        # loudnorm çıktısı stderr'de
        output = result.stderr
        start = output.rfind("{")
        end = output.rfind("}") + 1
        if start >= 0 and end > start:
            loudness_data = json.loads(output[start:end])
            return float(loudness_data.get("input_i", "-99"))
    except Exception as e:
        logger.warning(f"Loudness ölçümü başarısız: {e}")
    return None


def check_video(path: str) -> dict:
    path = str(path)
    logger.info(f"Video kontrol ediliyor: {path}")

    info = probe_video(path)

    duration = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / 1024 / 1024

    video_stream = next(
        (s for s in info["streams"] if s["codec_type"] == "video"), None
    )
    audio_stream = next(
        (s for s in info["streams"] if s["codec_type"] == "audio"), None
    )

    issues = []

    if not (MIN_DURATION <= duration <= MAX_DURATION):
        issues.append(f"Süre uygunsuz: {duration:.1f}sn (beklenen {MIN_DURATION}-{MAX_DURATION}sn)")

    if video_stream:
        w, h = video_stream.get("width"), video_stream.get("height")
        if w != EXPECTED_WIDTH or h != EXPECTED_HEIGHT:
            issues.append(f"Çözünürlük yanlış: {w}x{h} (beklenen {EXPECTED_WIDTH}x{EXPECTED_HEIGHT})")
    else:
        issues.append("Video stream bulunamadı")

    if not audio_stream:
        issues.append("Ses stream yok")

    if size_mb > 500:
        issues.append(f"Dosya çok büyük: {size_mb:.1f} MB (max 500 MB)")

    lufs = check_audio_loudness(path)

    result = {
        "status": "ok" if not issues else "failed",
        "duration": round(duration, 2),
        "size_mb": round(size_mb, 2),
        "resolution": f"{video_stream['width']}x{video_stream['height']}" if video_stream else "N/A",
        "has_audio": audio_stream is not None,
        "loudness_lufs": lufs,
        "issues": issues,
    }

    if issues:
        for issue in issues:
            logger.error(f"  ✗ {issue}")
        raise ValueError(f"Video kalite kontrolü başarısız: {'; '.join(issues)}")

    logger.success(
        f"Video geçti: {duration:.1f}sn, {result['resolution']}, "
        f"{size_mb:.1f}MB, LUFS={lufs}"
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video kalite kontrolü")
    parser.add_argument("video", help="MP4 dosya yolu")
    args = parser.parse_args()

    result = check_video(args.video)
    print(json.dumps(result, indent=2, ensure_ascii=False))
