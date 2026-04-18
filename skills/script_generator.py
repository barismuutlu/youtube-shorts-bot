"""
Script Generator — Claude API ile Rick & Morty tarzı İngilizce diyalog üretimi.
Girdi: konu (str) veya PDF metni (str)
Çıktı: JSON formatında script + SEO metadata
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

SYSTEM_PROMPT = """You are a YouTube Shorts scriptwriter creating Rick & Morty style educational dialogues.

Video structure (STRICT ORDER):
1. HOOK — Rick's first line must be a shocking, curiosity-triggering statement about a surprising fact or counterintuitive detail of the topic. Maximum 10 words. No greetings. Start mid-thought. This makes viewers stop scrolling.
2. CONVERSATION — Rick and Morty discuss the topic with real technical details, specific numbers, and mind-blowing facts. Rick explains with sarcasm and genius-level depth. Morty reacts with genuine curiosity and asks follow-up questions that lead to even more interesting facts.

Character rules:
- Rick: uses words like "Morty", "listen", "obviously", "genius", drops specific data (percentages, years, names, measurements)
- Morty: says "Wait, what?!", "Oh man", "That's insane", asks short clarifying questions
- Every line: maximum 12 words (must fit subtitle bar)
- Total duration: 45–58 seconds
- Language: English only
- emotion values: "hook", "explain", "excited", "sarcastic", "confused", "shocked", "happy"

The HOOK line must have emotion: "hook" and character: "rick".

Respond ONLY with valid JSON, no extra text:
{
  "title": "Topic title",
  "seo_title": "YouTube Shorts SEO-optimized title under 60 chars with power words",
  "seo_description": "2-3 sentence YouTube description with keywords, hook question, and relevant hashtags on new lines. Include #Shorts #RickAndMorty and 3-5 topic-specific hashtags.",
  "lines": [
    {
      "character": "rick",
      "text": "Hook line here — shocking fact.",
      "duration": 2.8,
      "emotion": "hook"
    },
    {
      "character": "morty",
      "text": "Wait, what?! How is that possible?",
      "duration": 2.1,
      "emotion": "shocked"
    }
  ],
  "total_duration": 48.0
}"""

USER_PROMPT_TEMPLATE = """Topic: {topic}

Write a Rick and Morty YouTube Shorts script about this topic.
- First line (hook): Rick says ONE shocking, specific, counterintuitive fact about this topic. No intro, no "Hey Morty", just the fact — raw and surprising.
- Then 8–11 more lines of back-and-forth with real technical details, specific numbers, named algorithms/people/events relevant to the topic.
- Total: 9–12 lines, 45–58 seconds.
- SEO title: punchy, 50–60 chars, include the topic keyword and a power phrase like "EXPLAINED", "You Won't Believe", "Mind-Blowing", etc.
- SEO description: start with a hook question, 2-3 sentences, end with relevant hashtags."""


def topic_to_slug(topic: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", topic.lower())
    slug = re.sub(r"[\s-]+", "_", slug).strip("_")
    return slug[:50]


def generate_script(topic: str = None, pdf_path: str = None) -> dict:
    if not topic and not pdf_path:
        raise ValueError("topic or pdf_path required")

    content = topic
    if pdf_path:
        if pdf_extract is None:
            raise ImportError("pdfminer.six not installed: pip install pdfminer.six")
        raw = pdf_extract(pdf_path)
        content = raw[:2000].strip()
        logger.info(f"PDF read: {pdf_path} ({len(content)} chars)")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    log_content = content[:60] + "..." if len(content) > 60 else content
    logger.info(f"Generating script: '{log_content}'")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(topic=content)}
        ],
    )

    raw_text = response.content[0].text.strip()

    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not json_match:
        raise ValueError(f"No valid JSON from Claude:\n{raw_text}")

    script = json.loads(json_match.group())
    _validate_script(script)

    if topic:
        script["topic_slug"] = topic_to_slug(topic)

    logger.success(
        f"Script ready: {len(script['lines'])} lines, {script['total_duration']:.1f}s | "
        f"SEO: \"{script.get('seo_title', 'N/A')}\""
    )
    return script


def _validate_script(script: dict):
    assert "title" in script, "title missing"
    assert "lines" in script and len(script["lines"]) > 0, "lines empty"
    assert "total_duration" in script, "total_duration missing"
    assert "seo_title" in script, "seo_title missing"
    assert "seo_description" in script, "seo_description missing"
    assert 40 <= script["total_duration"] <= 62, f"Duration out of range: {script['total_duration']}s"

    first = script["lines"][0]
    assert first.get("character") == "rick", "First line must be Rick (hook)"
    assert first.get("emotion") == "hook", "First line must have emotion='hook'"

    for i, line in enumerate(script["lines"]):
        assert line.get("character") in ("rick", "morty"), f"Line {i}: invalid character"
        assert line.get("text"), f"Line {i}: text empty"
        assert line.get("duration", 0) > 0, f"Line {i}: duration zero"


def save_script(script: dict, session_id: str = None) -> Path:
    if session_id is None:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    logger.info(f"Script saved: {path}")
    return path


def save_seo_metadata(script: dict, topic_slug: str) -> Path:
    seo_path = OUTPUT_DIR / f"{topic_slug}_seo.txt"
    with open(seo_path, "w", encoding="utf-8") as f:
        f.write(f"TITLE:\n{script.get('seo_title', '')}\n\n")
        f.write(f"DESCRIPTION:\n{script.get('seo_description', '')}\n")
    logger.info(f"SEO metadata saved: {seo_path}")
    return seo_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rick & Morty script generator")
    parser.add_argument("--topic", type=str, help="Topic to process")
    parser.add_argument("--pdf", type=str, help="PDF file path")
    parser.add_argument("--session", type=str, help="Session ID (optional)")
    args = parser.parse_args()

    if not args.topic and not args.pdf:
        parser.error("--topic or --pdf required")

    script = generate_script(topic=args.topic, pdf_path=args.pdf)
    path = save_script(script, args.session)

    slug = script.get("topic_slug", args.session or "output")
    save_seo_metadata(script, slug)

    print("\n--- GENERATED SCRIPT ---")
    print(json.dumps(script, ensure_ascii=False, indent=2))
    print(f"\nSaved: {path}")
