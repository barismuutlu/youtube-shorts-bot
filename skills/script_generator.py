"""
Script Generator — Claude API ile Rick & Morty tarzı diyalog üretimi.
Girdi: konu (str) veya PDF metni (str)
Çıktı: JSON formatında script dosyası
"""

import os
import json
import argparse
import re
from pathlib import Path
from datetime import datetime

import anthropic
from dotenv import load_dotenv
from loguru import logger

try:
    from pdfminer.high_level import extract_text as pdf_extract
except ImportError:
    pdf_extract = None

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "scripts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """Sen bir YouTube Shorts senaryo yazarısın. Rick Sanchez ve Morty Smith'in diyaloglarını yazıyorsun.

Kurallar:
- Rick her şeyi bilir, keskin, alaycı ve zeki; "Morty" kelimesini sık kullanır
- Morty meraklı, biraz şaşkın ama sevimli
- Her replik maksimum 12 kelime (altyazıya sığsın)
- Toplam 45-58 saniye arası olmalı
- Her replik için tahmini konuşma süresi saniye cinsinden hesapla (yaklaşık: kelime_sayısı × 0.4)
- emotion değeri: "explain", "excited", "sarcastic", "confused", "shocked", "happy" birinden biri olmalı

Yanıtını SADECE aşağıdaki JSON formatında döndür, başka hiçbir şey yazma:
{
  "title": "Konu başlığı",
  "lines": [
    {
      "character": "rick",
      "text": "Replik metni",
      "duration": 3.2,
      "emotion": "explain"
    }
  ],
  "total_duration": 45.0
}"""

USER_PROMPT_TEMPLATE = """Konu: {topic}

Rick ve Morty bu konuyu kısa bir YouTube Shorts videosunda ele alıyor. Türkçe yaz.
Toplam 8-12 replik, 45-58 saniye arası."""


def generate_script(topic: str = None, pdf_path: str = None) -> dict:
    if not topic and not pdf_path:
        raise ValueError("topic veya pdf_path gerekli")

    content = topic
    if pdf_path:
        if pdf_extract is None:
            raise ImportError("pdfminer.six kurulu değil: pip install pdfminer.six")
        raw = pdf_extract(pdf_path)
        # İlk 2000 karakter yeterli
        content = raw[:2000].strip()
        logger.info(f"PDF okundu: {pdf_path} ({len(content)} karakter)")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    logger.info(f"Script üretiliyor: '{content[:60]}...' " if len(content) > 60 else f"Script üretiliyor: '{content}'")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(topic=content)}
        ],
    )

    raw_text = response.content[0].text.strip()

    # JSON bloğunu temizle (```json ... ``` varsa)
    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not json_match:
        raise ValueError(f"Claude'dan geçerli JSON alınamadı:\n{raw_text}")

    script = json.loads(json_match.group())
    _validate_script(script)

    logger.success(f"Script hazır: {len(script['lines'])} replik, {script['total_duration']:.1f}sn")
    return script


def _validate_script(script: dict):
    assert "title" in script, "title eksik"
    assert "lines" in script and len(script["lines"]) > 0, "lines boş"
    assert "total_duration" in script, "total_duration eksik"
    assert 40 <= script["total_duration"] <= 60, f"Süre uygunsuz: {script['total_duration']}sn"
    for i, line in enumerate(script["lines"]):
        assert line.get("character") in ("rick", "morty"), f"Satır {i}: geçersiz karakter"
        assert line.get("text"), f"Satır {i}: metin boş"
        assert line.get("duration", 0) > 0, f"Satır {i}: süre sıfır"


def save_script(script: dict, session_id: str = None) -> Path:
    if session_id is None:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    logger.info(f"Script kaydedildi: {path}")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rick & Morty script üretici")
    parser.add_argument("--topic", type=str, help="İşlenecek konu")
    parser.add_argument("--pdf", type=str, help="PDF dosya yolu")
    parser.add_argument("--session", type=str, help="Session ID (opsiyonel)")
    args = parser.parse_args()

    if not args.topic and not args.pdf:
        parser.error("--topic veya --pdf gerekli")

    script = generate_script(topic=args.topic, pdf_path=args.pdf)
    path = save_script(script, args.session)

    print("\n--- ÜRETILEN SCRIPT ---")
    print(json.dumps(script, ensure_ascii=False, indent=2))
    print(f"\nKaydedildi: {path}")
