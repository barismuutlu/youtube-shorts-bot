#!/bin/bash
# YouTube Shorts Bot — Kurulum scripti

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== YouTube Shorts Bot Kurulum ==="

# Python sanal ortam
echo "[1/4] Python sanal ortam (venv) kuruluyor..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "  .venv oluşturuldu"
else
  echo "  .venv zaten mevcut, atlandı"
fi

echo "[2/4] Python paketleri kuruluyor (.venv içine)..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt

# Node.js bağımlılıkları (Remotion)
echo "[3/4] Remotion/Node.js paketleri kuruluyor..."
cd remotion
npm install
cd ..

# .env dosyası oluştur
if [ ! -f .env ]; then
  echo "[4/4] .env dosyası oluşturuluyor (.env.example'dan)..."
  cp .env.example .env
  echo "  ⚠️  .env dosyasını API anahtarlarınızla doldurun!"
else
  echo "[4/4] .env zaten mevcut, atlandı."
fi

echo ""
echo "=== Kurulum tamamlandı ==="
echo ""
echo "Python çalıştırmak için venv'i aktif et:"
echo "  source .venv/bin/activate"
echo ""
echo "Veya doğrudan:"
echo "  .venv/bin/python skills/script_generator.py --topic 'Kara delikler'"
echo ""
echo "Remotion önizleme:"
echo "  cd remotion && npx remotion studio"
