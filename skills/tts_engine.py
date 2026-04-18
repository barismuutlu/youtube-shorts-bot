"""
TTS Engine — ElevenLabs API ile Rick & Morty seslendirmesi.
Girdi: script JSON
Çıktı: MP3 dosyaları + gerçek zamanlama ile güncellenmiş script
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

from elevenlabs import ElevenLabs
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
AUDIO_OUTPUT_DIR = BASE_DIR / "output" / "audio"
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Remotion'ın okuyacağı statik dizin
REMOTION_AUDIO_DIR = BASE_DIR / "remotion" / "public" / "audio"
REMOTION_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

ELEVENLABS_SETTINGS = {
    "stability": 0.35,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": True,
}


def _get_audio_duration(mp3_path: Path) -> float:
    """MP3 dosyasının gerçek süresini ffprobe ile okur."""
    import subprocess as _sp
    result = _sp.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(mp3_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return float(result.stdout.strip())
    # ffprobe başarısız olursa mutagen dene
    try:
        from mutagen.mp3 import MP3
        return MP3(str(mp3_path)).info.length
    except Exception:
        return None


def synthesize_line(
    client: ElevenLabs,
    text: str,
    voice_id: str,
    output_path: Path,
) -> float:
    """Tek bir repliği seslendir, MP3 kaydet, gerçek süreyi döndür."""
    audio_generator = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings={
            "stability": ELEVENLABS_SETTINGS["stability"],
            "similarity_boost": ELEVENLABS_SETTINGS["similarity_boost"],
            "style": ELEVENLABS_SETTINGS["style"],
            "use_speaker_boost": ELEVENLABS_SETTINGS["use_speaker_boost"],
        },
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio_generator:
            f.write(chunk)

    duration = _get_audio_duration(output_path)
    if duration is None:
        # Son çare: kelime başına ~0.5 saniye (ElevenLabs için daha gerçekçi)
        duration = len(text.split()) * 0.5
        logger.warning(f"ffprobe/mutagen başarısız, süre tahmin edildi: {duration:.2f}sn")

    logger.debug(f"  {output_path.name} → {duration:.2f}sn")
    return duration


def run_tts(script: dict, session_id: str) -> dict:
    """
    Script'teki tüm replikler için TTS üret.
    Gerçek sürelerle script'i günceller ve geri döndürür.
    """
    rick_voice_id = os.environ.get("RICK_VOICE_ID")
    morty_voice_id = os.environ.get("MORTY_VOICE_ID")

    if not rick_voice_id or not morty_voice_id:
        raise EnvironmentError("RICK_VOICE_ID ve MORTY_VOICE_ID .env dosyasında tanımlanmamış")

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

    session_dir = AUDIO_OUTPUT_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Remotion için de aynı session dizini
    remotion_session_dir = REMOTION_AUDIO_DIR / session_id
    remotion_session_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"TTS başlıyor: {len(script['lines'])} replik, session={session_id}")

    updated_lines = []
    total_duration = 0.0
    counters = {"rick": 0, "morty": 0}

    for line in script["lines"]:
        char = line["character"]
        counters[char] += 1
        idx = counters[char]
        filename = f"{char}_{idx:03d}.mp3"

        voice_id = rick_voice_id if char == "rick" else morty_voice_id

        # Hem output/ hem remotion/public/audio/ altına kaydet
        mp3_output = session_dir / filename
        mp3_remotion = remotion_session_dir / filename

        real_duration = synthesize_line(client, line["text"], voice_id, mp3_output)

        # Remotion için symlink yerine kopyala
        import shutil
        shutil.copy2(mp3_output, mp3_remotion)

        updated_line = dict(line)
        updated_line["duration"] = real_duration
        updated_line["audio_file"] = filename
        updated_lines.append(updated_line)
        total_duration += real_duration

    script = dict(script)
    script["lines"] = updated_lines
    script["total_duration"] = round(total_duration, 2)
    script["session_id"] = session_id
    script["audio_dir"] = str(session_dir)

    logger.success(f"TTS tamamlandı: toplam {total_duration:.1f}sn, {len(updated_lines)} dosya")
    return script


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ElevenLabs TTS seslendirme")
    parser.add_argument("--script", required=True, help="Script JSON dosya yolu")
    parser.add_argument("--session", type=str, help="Session ID (opsiyonel)")
    args = parser.parse_args()

    with open(args.script, encoding="utf-8") as f:
        script_data = json.load(f)

    session_id = args.session or datetime.now().strftime("%Y%m%d_%H%M%S")
    updated = run_tts(script_data, session_id)

    out_path = Path(args.script).parent / f"{Path(args.script).stem}_tts.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)

    print(f"\nGüncellenen script kaydedildi: {out_path}")
    print(f"Toplam süre: {updated['total_duration']}sn")
