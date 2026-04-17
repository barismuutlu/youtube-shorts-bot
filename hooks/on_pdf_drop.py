"""
on_pdf_drop.py — input/pdfs/ klasörünü izler, yeni PDF gelince pipeline'ı tetikler.
Bağımlılık: pip install watchdog
"""

import sys
import time
import shutil
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
PDF_DIR = BASE_DIR / "input" / "pdfs"
PROCESSED_DIR = BASE_DIR / "input" / "pdfs" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Ana pipeline'ı import et
sys.path.insert(0, str(BASE_DIR))


class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".pdf" and path.parent == PDF_DIR:
            logger.info(f"Yeni PDF algılandı: {path.name}")
            # Kısa bekleme: dosya tam yazılsın
            time.sleep(2)
            self._process(path)

    def _process(self, path: Path):
        try:
            from main import run_pipeline
            run_pipeline(source_type="pdf", content=str(path))
            # Başarılıysa processed/ klasörüne taşı
            shutil.move(str(path), str(PROCESSED_DIR / path.name))
            logger.success(f"PDF işlendi ve taşındı: {path.name}")
        except Exception as e:
            logger.error(f"PDF işlenirken hata: {e}")


def watch():
    logger.info(f"PDF klasörü izleniyor: {PDF_DIR}")
    event_handler = PDFHandler()
    observer = Observer()
    observer.schedule(event_handler, str(PDF_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("PDF izleyici durduruldu")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    watch()
