# CLAUDE.md — YouTube Shorts Otomasyon Projesi
## Minecraft Parkour + Rick & Morty AI Seslendirmesi

---

## 📌 Proje Özeti

Bu proje; Minecraft parkur videolarının arka planda oynatıldığı, Rick ve Morty karakterlerinin bir konu veya PDF üzerinden AI tarafından üretilen diyaloglarla konuştuğu, kısa dikey (YouTube Shorts formatında) videolar üretir ve bunları otomatik olarak Google Drive'a yükler.

**Çıktı:** 9:16 dikey video, 30–60 sn, Shorts optimizasyonlu  
**Hedef:** Düzenli içerik akışı — insan müdahalesi sadece YouTube yükleme adımında  

---

## 🗂 Proje Dosya Yapısı

```
youtube-shorts-bot/
├── CLAUDE.md                        ← Bu dosya
├── .env                             ← API anahtarları (git'e ekleme!)
├── main.py                          ← Ana orkestrasyon scripti (Python)
├── config.yaml                      ← Genel ayarlar
│
├── skills/                          ← Python skill'leri (veri üretimi)
│   ├── script_generator.py          ← Claude API ile script üretimi
│   ├── tts_engine.py                ← ElevenLabs TTS seslendirme
│   ├── video_renderer.py            ← Remotion render tetikleyici (subprocess)
│   ├── quality_checker.py           ← Video doğrulama
│   └── drive_uploader.py            ← Google Drive yükleme
│
├── hooks/                           ← Olay tetikleyiciler
│   ├── on_pdf_drop.py               ← PDF klasörüne dosya gelince tetikle
│   ├── on_schedule.py               ← Zamanlayıcı (günlük/haftalık)
│   └── on_complete.py               ← Upload sonrası bildirim
│
├── remotion/                        ← Remotion projesi (Node.js / React)
│   ├── package.json
│   ├── tsconfig.json
│   ├── remotion.config.ts
│   ├── public/                      ← Remotion'ın statik dosyaları
│   │   ├── footage/                 ← Minecraft parkur klipleri
│   │   │   ├── parkour_001.mp4
│   │   │   └── ...
│   │   ├── characters/              ← Rick & Morty transparent PNG'leri
│   │   │   ├── rick_idle.png
│   │   │   ├── rick_talk.png
│   │   │   ├── morty_idle.png
│   │   │   └── morty_talk.png
│   │   ├── audio/                   ← TTS MP3'leri (Python tarafından doldurulur)
│   │   │   └── {session_id}/
│   │   │       ├── rick_001.mp3
│   │   │       └── morty_002.mp3
│   │   └── fonts/
│   │       └── Bangers.ttf
│   └── src/
│       ├── index.ts                 ← Remotion giriş noktası
│       ├── Root.tsx                 ← Composition tanımları
│       ├── ShortVideo.tsx           ← Ana kompozisyon bileşeni
│       └── components/
│           ├── ParkourBackground.tsx  ← Minecraft video katmanı
│           ├── CharacterOverlay.tsx   ← Rick/Morty PNG + konuşma animasyonu
│           ├── SubtitleLayer.tsx      ← Zamanlamalı altyazı bileşeni
│           └── DimOverlay.tsx         ← Okunabilirlik için karartma katmanı
│
├── input/
│   ├── topics.txt                   ← İşlenecek konu listesi
│   └── pdfs/                        ← PDF materyal klasörü
│
└── output/
    ├── scripts/                     ← Üretilen scriptler (.json)
    ├── audio/                       ← TTS ses dosyaları (session bazlı)
    ├── videos/                      ← Final render'lar (.mp4)
    └── logs/                        ← İşlem logları
```

---

## 🔑 Ortam Değişkenleri (.env)

```env
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...

# ElevenLabs Voice ID'leri (Rick & Morty sesleri için clone veya benzer)
RICK_VOICE_ID=...
MORTY_VOICE_ID=...

# Google Drive (MCP ile yönetiliyor, ek key gerekmeyebilir)
GOOGLE_DRIVE_FOLDER_ID=...  ← Shorts'ların yükleneceği klasör ID'si

# Opsiyonel: Zamanlayıcı
SCHEDULE_TIME=09:00         ← Her gün saat kaçta üretilsin
SCHEDULE_DAYS=mon,wed,fri   ← Hangi günler
```

---

## ⚙️ Genel Ayarlar (config.yaml)

```yaml
video:
  width: 1080
  height: 1920
  fps: 30
  max_duration: 58          # Shorts için 60sn altında tut
  min_duration: 30

characters:
  rick:
    position: bottom-left   # Ekrandaki konumu
    scale: 0.35             # Ekran genişliğine oranı
  morty:
    position: bottom-right
    scale: 0.32

subtitles:
  font: bangers.ttf
  size: 72
  color: white
  stroke_color: black
  stroke_width: 4
  position: center          # Ekranın ortası

script:
  language: tr              # Türkçe veya en
  style: "Rick ve Morty"
  lines_per_character: 3-5  # Her karakter kaç replik söylesin
  max_words_per_line: 8     # Altyazı satır uzunluğu

drive:
  upload_folder: "YouTube Shorts Queue"
  naming: "{date}_{topic_slug}_{index}"
```

---

## 🧠 Skills (Yeniden Kullanılabilir Modüller)

### Skill 1: `script_generator.py`
**Ne yapar:** Verilen konu veya PDF içeriğinden Rick & Morty tarzı diyalog scripti üretir.

**Kullandığı:** Claude API (`claude-sonnet-4-5`)

**Girdi:** `topic: str` veya `pdf_text: str`  
**Çıktı:** JSON format script

```python
# Örnek çıktı formatı:
{
  "title": "Kuantum Fiziği",
  "lines": [
    {
      "character": "rick",
      "text": "Morty, kuantum dolanıklığı dediğimizde aslında...",
      "duration": 3.2,
      "emotion": "explain"
    },
    {
      "character": "morty",
      "text": "A-ama Rick bu nasıl mümkün olabilir ki?",
      "duration": 2.1,
      "emotion": "confused"
    }
  ],
  "total_duration": 45.0
}
```

**Sistem Promptu:**
```
Sen Rick Sanchez'sin ve Morty ile kısa ama bilgilendirici bir YouTube Shorts 
diyaloğu yazıyorsun. Kural: 
- Rick her şeyi bilir, keskin ve alaycıdır, "Morty" kelimesini sık kullanır
- Morty meraklı, biraz şaşkın ama sevimli
- Her replik max 12 kelime (altyazıya sığsın)
- Toplam 30-55 saniye arası
- JSON formatında döndür: {lines: [{character, text, duration, emotion}]}
- Konu: {TOPIC}
```

---

### Skill 2: `tts_engine.py`
**Ne yapar:** Script satırlarını ElevenLabs API ile seslendirip MP3 dosyaları üretir.

**Kullandığı:** ElevenLabs API

**Girdi:** Script JSON  
**Çıktı:** `audio/rick_001.mp3`, `audio/morty_001.mp3`, ... + timing data

**Notlar:**
- Rick ve Morty için farklı Voice ID kullan
- Her replik ayrı dosya olarak kaydet (video sync için şart)
- `stability=0.35, similarity_boost=0.75` ayarları karakteristik ses için

---

### Skill 3: `video_renderer.py` (Python) + `remotion/src/` (React)
**Ne yapar:** Script JSON ve audio dosyalarını Remotion'a props olarak geçirir, `npx remotion render` ile headless render tetikler.

**Kullandığı:** `remotion` (Node.js), Python `subprocess`

**Mimari — 2 katman:**
- **Python tarafı (`video_renderer.py`):** Props JSON'ı hazırlar, Remotion CLI'ı subprocess ile çağırır, çıktı dosyasını taşır.
- **React tarafı (`remotion/src/`):** Kompozisyonu frame-by-frame render eden bileşenler.

**Python tarafı:**
```python
import subprocess, json, shutil

def render_video(script: dict, session_id: str, output_path: str):
    props = {
        "sessionId": session_id,
        "lines": script["lines"],
        "totalDurationSec": script["total_duration"],
        "footageFile": "parkour_001.mp4"   # rastgele seçilebilir
    }
    props_file = f"/tmp/{session_id}_props.json"
    with open(props_file, "w") as f:
        json.dump(props, f)

    subprocess.run([
        "npx", "remotion", "render",
        "src/index.ts",          # giriş noktası
        "ShortVideo",            # composition ID
        output_path,
        "--props", props_file,
        "--codec", "h264",
        "--log", "verbose"
    ], cwd="remotion/", check=True)
```

**Remotion Composition Katmanları (`ShortVideo.tsx`):**
```tsx
// Katmanlar (alt'tan üste):
// 1. <ParkourBackground>    — döngülü Minecraft videosu, 9:16 crop
// 2. <DimOverlay>           — %35 siyah overlay (okunabilirlik)
// 3. <CharacterOverlay>     — konuşan karakter PNG + bobbing animasyonu
// 4. <SubtitleLayer>        — zamanlamalı altyazı, Bangers font
// 5. <Audio>                — sıralı TTS ses dosyaları

export const ShortVideo: React.FC<ShortVideoProps> = ({ lines, sessionId }) => {
  return (
    <AbsoluteFill>
      <ParkourBackground />
      <DimOverlay opacity={0.35} />
      {lines.map((line, i) => (
        <Sequence key={i} from={line.startFrame} durationInFrames={line.durationFrames}>
          <CharacterOverlay character={line.character} emotion={line.emotion} />
          <Audio src={staticFile(`audio/${sessionId}/${line.character}_${i}.mp3`)} />
        </Sequence>
      ))}
      <SubtitleLayer lines={lines} />
    </AbsoluteFill>
  );
};
```

**Remotion Bileşenleri:**

`ParkourBackground.tsx` — Minecraft footage döngüsü:
```tsx
import { Video, Loop, staticFile } from "remotion";
export const ParkourBackground = ({ file }: { file: string }) => (
  <AbsoluteFill>
    <Loop>
      <Video src={staticFile(`footage/${file}`)}
             style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </Loop>
  </AbsoluteFill>
);
```

`CharacterOverlay.tsx` — Konuşma animasyonu:
```tsx
import { useCurrentFrame, spring, useVideoConfig, Img, staticFile } from "remotion";
export const CharacterOverlay = ({ character, emotion }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Bobbing: konuşurken hafif yukarı-aşağı sallanma
  const bobY = spring({ frame, fps, from: 0, to: -8, durationInFrames: 6 });
  const imgSrc = emotion === "talk"
    ? staticFile(`characters/${character}_talk.png`)
    : staticFile(`characters/${character}_idle.png`);
  const isRick = character === "rick";
  return (
    <AbsoluteFill style={{
      bottom: 0, [isRick ? "left" : "right"]: 20,
      top: "auto", transform: `translateY(${bobY}px)`
    }}>
      <Img src={imgSrc} style={{ height: "40%", objectFit: "contain" }} />
    </AbsoluteFill>
  );
};
```

`SubtitleLayer.tsx` — Zamanlamalı altyazı:
```tsx
import { useCurrentFrame, interpolate } from "remotion";
export const SubtitleLayer = ({ lines }) => {
  const frame = useCurrentFrame();
  const active = lines.find(l => frame >= l.startFrame &&
                                  frame < l.startFrame + l.durationFrames);
  if (!active) return null;
  const opacity = interpolate(frame, [active.startFrame, active.startFrame + 3], [0, 1]);
  const color = active.character === "rick" ? "#00FF88" : "#FFD700";
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center",
                           top: "45%", bottom: "auto" }}>
      <div style={{ fontFamily: "Bangers", fontSize: 72, color: "white",
                    WebkitTextStroke: `4px black`, opacity, textAlign: "center",
                    padding: "0 40px" }}>
        <span style={{ color }}>{active.character.toUpperCase()}: </span>
        {active.text}
      </div>
    </AbsoluteFill>
  );
};
```

**Remotion Config (`remotion.config.ts`):**
```ts
import { Config } from "@remotion/cli/config";
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setConcurrency(4);         // render hızı için
```

**Root.tsx — Composition tanımı:**
```tsx
import { Composition } from "remotion";
import { ShortVideo } from "./ShortVideo";
export const RemotionRoot = () => (
  <Composition
    id="ShortVideo"
    component={ShortVideo}
    durationInFrames={1740}     // ~58sn × 30fps, props'tan override edilir
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{ lines: [], sessionId: "test", totalDurationSec: 45 }}
  />
);
```

---

### Skill 4: (Kaldırıldı — Remotion'a taşındı)
Altyazı render artık `SubtitleLayer.tsx` React bileşeni içinde yapılıyor. Ayrı Python skill'e gerek yok.

**Avantajlar (ffmpeg'e göre):**
- Altyazı animasyonu (fade-in, word highlight) React state ile çok kolay
- Karakter bobbing/konuşma animasyonu `spring()` ile 3 satır kod
- Preview: `npx remotion studio` ile tarayıcıda anlık önizleme
- Katmanlar React component'ları — değiştirmesi, test etmesi çok daha kolay
- Props ile dinamik — her video için yeni JSON geçmek yeterli

---

### Skill 5: `quality_checker.py`
**Ne yapar:** Final videoyu kontrol eder, upload öncesi onaylar.

**Kontroller:**
- Süre 30-58 saniye arası mı?
- Çözünürlük 1080x1920 mi?
- Ses var mı ve seviye uygun mu? (-14 LUFS hedef)
- Dosya boyutu <500MB mi?
- Video bozuk mu? (`ffprobe` CLI ile — ffmpeg-python değil, sadece binary)

```python
import subprocess, json

def check_video(path: str) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    duration = float(info["format"]["duration"])
    assert 28 <= duration <= 60, f"Süre uygunsuz: {duration}sn"
    video_stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert video_stream["width"] == 1080, "Genişlik 1080 değil"
    assert video_stream["height"] == 1920, "Yükseklik 1920 değil"
    return {"status": "ok", "duration": duration, "size_mb": ...}
```

---

### Skill 6: `drive_uploader.py`
**Ne yapar:** Google Drive MCP kullanarak videoyu belirlenen klasöre yükler.

**MCP:** Google Drive MCP (zaten bağlı ✅)

**Çıktı:** Drive linki + dosya metadata JSON

---

## 🪝 Hooks (Olay Tetikleyiciler)

### Hook 1: `on_pdf_drop.py` — PDF Tetikleyici
**Ne zaman:** `input/pdfs/` klasörüne yeni PDF bırakıldığında

**Nasıl:** `watchdog` kütüphanesi ile klasör izleme

```python
# Pseudo kod:
def on_pdf_added(filepath):
    text = extract_pdf_text(filepath)
    run_pipeline(source="pdf", content=text)
    move_to_processed(filepath)
```

**Kullanım:** PDF'i klasöre sürükle-bırak → 5 dakika içinde video Drive'da

---

### Hook 2: `on_schedule.py` — Zamanlayıcı
**Ne zaman:** `config.yaml`'daki SCHEDULE_TIME ve SCHEDULE_DAYS'e göre

**Kullandığı:** `schedule` veya `APScheduler` kütüphanesi

**Mantık:** `topics.txt`'ten sıradaki konuyu al → pipeline'ı çalıştır → konuyu işaretle

---

### Hook 3: `on_complete.py` — Tamamlama Bildirimi
**Ne zaman:** Her başarılı upload sonrası

**Yapabilecekleri:**
- Terminal'e özet yazdır
- `output/logs/history.json`'a kayıt ekle
- Opsiyonel: e-posta veya Telegram mesajı gönder

---

## 🔌 MCP Entegrasyonları

### Google Drive MCP ✅ (Zaten Bağlı)
- **Kullanım:** Final video upload, klasör yönetimi
- **Server URL:** `https://drivemcp.googleapis.com/mcp/v1`
- **İşlemler:** `create_file`, `list_files`, `get_file`

**Artifact'te API çağrısı örneği:**
```javascript
mcp_servers: [{
  type: "url",
  url: "https://drivemcp.googleapis.com/mcp/v1",
  name: "google-drive"
}]
```

---

## 📋 Adım Adım Uygulama Planı

### AŞAMA 0: Hazırlık (1-2 saat)
- [ ] Repository oluştur, Python venv kur
- [ ] Python bağımlılıkları: `pip install anthropic elevenlabs watchdog APScheduler pdfminer.six python-dotenv PyYAML loguru`
- [ ] Node.js bağımlılıkları (Remotion için):
  ```bash
  cd remotion/
  npm init -y
  npm install remotion @remotion/cli @remotion/player react react-dom
  npm install -D typescript @types/react
  ```
- [ ] `.env` dosyasını doldur
- [ ] ElevenLabs'ta Rick ve Morty seslerini bul/clone et, Voice ID'leri kaydet
- [ ] Minecraft parkur videolarını `remotion/public/footage/` klasörüne koy
- [ ] Rick ve Morty transparent PNG'lerini `remotion/public/characters/` klasörüne koy
- [ ] Bangers fontunu `remotion/public/fonts/` klasörüne koy
- [ ] Remotion studio ile ilk açılışı test et: `cd remotion && npx remotion studio`
- [ ] Google Drive'da "YouTube Shorts Queue" klasörü oluştur, ID'sini kaydet

---

### AŞAMA 1: Script Generator Skill (2-3 saat)
**Hedef:** `skills/script_generator.py` çalışır hale getir

Adımlar:
1. Claude API bağlantısını test et
2. Sistem promptunu yaz ve dene (Türkçe/İngilizce seçeneği)
3. PDF okuma entegrasyonu ekle (`pdfminer.six`)
4. JSON output validasyonu ekle
5. Test: 5 farklı konu ile test et, çıktıları `output/scripts/` klasörüne kaydet

**Test komutu:**
```bash
python skills/script_generator.py --topic "Kara delikler nasıl çalışır"
python skills/script_generator.py --pdf input/pdfs/test.pdf
```

---

### AŞAMA 2: TTS Engine Skill (2-3 saat)
**Hedef:** `skills/tts_engine.py` çalışır hale getir

Adımlar:
1. ElevenLabs API bağlantısını test et
2. Rick ve Morty voice ID'leri ile test ses üret
3. Her replik için ayrı MP3 kaydet (naming: `rick_001.mp3`, `morty_002.mp3`)
4. Gerçek süre bilgisini (MP3 süresinden) oku ve script JSON'ı güncelle
5. Ses dosyalarını `output/audio/{session_id}/` klasörüne kaydet

**Test komutu:**
```bash
python skills/tts_engine.py --script output/scripts/test_script.json
```

---

### AŞAMA 3: Remotion Kompozisyonu (4-6 saat) ← En kritik aşama
**Hedef:** `remotion/src/` altındaki tüm bileşenler çalışır, `npx remotion render` ile video çıkar

Alt adımlar:
1. **3a — Root & Composition:** `Root.tsx` ve `index.ts` kur, `npx remotion studio` ile açıl
2. **3b — ParkourBackground:** Footage'ı `<Loop><Video>` ile döngüye al, `objectFit: cover` ile 9:16'ya doldur
3. **3c — DimOverlay:** `<AbsoluteFill style={{background: "rgba(0,0,0,0.35)"}}/>` — tek satır
4. **3d — CharacterOverlay:** Karakter PNG'lerini `<Sequence>` ile doğru frame aralıklarında göster, `spring()` ile bobbing
5. **3e — SubtitleLayer:** `useCurrentFrame()` ile aktif repliği bul, `interpolate()` ile fade-in
6. **3f — Audio sync:** `<Audio src={staticFile(...)} />` her Sequence içine, otomatik sync
7. **3g — Props bridge:** Python'dan `--props props.json` ile dinamik veri geçişini test et
8. **3h — Final render testi:** `npx remotion render src/index.ts ShortVideo out/test.mp4`

**Kritik: Frame hesaplama (Python tarafında yapılır):**
```python
FPS = 30
def sec_to_frames(sec: float) -> int:
    return round(sec * FPS)

# Script JSON'a startFrame ekle
cumulative = 0
for line in script["lines"]:
    line["startFrame"] = sec_to_frames(cumulative)
    line["durationFrames"] = sec_to_frames(line["duration"])
    cumulative += line["duration"]
```

**Remotion render komutu (Python subprocess ile):**
```bash
npx remotion render src/index.ts ShortVideo ../../output/videos/{session_id}.mp4 \
  --props /tmp/{session_id}_props.json \
  --codec h264 \
  --height 1920 --width 1080
```

**Preview için (geliştirme sırasında):**
```bash
cd remotion && npx remotion studio
# Tarayıcıda http://localhost:3000 — gerçek zamanlı önizleme
```

---

### AŞAMA 4: Quality Checker (1 saat)
**Hedef:** `skills/quality_checker.py` çalışır hale getir

Remotion render'dan çıkan MP4'ü `ffprobe` CLI ile kontrol et (ffmpeg-python paketi gerekmez, sadece binary):

```bash
ffprobe -v quiet -print_format json -show_format -show_streams output/videos/test.mp4
```

---

### AŞAMA 5: Google Drive Upload (1-2 saat)
**Hedef:** `skills/drive_uploader.py` çalışır hale getir

MCP üzerinden veya Google Drive Python SDK ile:
```python
def upload_to_drive(video_path, folder_id, filename):
    # Google Drive MCP kullanarak upload
    # Dönüş: {"file_id": "...", "web_link": "..."}
```

---

### AŞAMA 6: Ana Orkestrasyon (1-2 saat)
**Hedef:** `main.py` tüm skill'leri sırayla çağırır

```python
# main.py akışı:
def run_pipeline(source_type, content):
    session_id = generate_session_id()
    
    # 1. Script üret
    script = script_generator.run(content)
    save(script, f"output/scripts/{session_id}.json")
    
    # 2. TTS
    audio_files = tts_engine.run(script, session_id)
    
    # 3. Video compose
    video_path = video_composer.run(script, audio_files, session_id)
    
    # 4. Kalite kontrol
    quality_checker.check(video_path)
    
    # 5. Drive'a yükle
    result = drive_uploader.upload(video_path)
    
    # 6. Log
    on_complete.notify(session_id, result)
```

---

### AŞAMA 7: Hooks Aktivasyonu (1 saat)
**Hedef:** PDF bırakma ve zamanlayıcı hook'larını çalıştır

```bash
# PDF izleyici başlat
python hooks/on_pdf_drop.py &

# Zamanlayıcı başlat
python hooks/on_schedule.py &
```

---

### AŞAMA 8: Test & İterasyon (2-3 saat)
- 3 farklı konuyla uçtan uca test
- 1 PDF ile uçtan uca test
- Drive'a yüklenen dosyaları kontrol et
- Video kalitesini değerlendir, promptları/ayarları gerekirse güncelle

---

## 🎯 Öneri: Hazır Kütüphane & Araç Listesi

| İş | Araç | Notlar |
|---|---|---|
| Script üretimi | `anthropic` SDK (Python) | Claude Sonnet 4.5 kullan |
| PDF okuma | `pdfminer.six` (Python) | Hafif ve güvenilir |
| TTS | `elevenlabs` SDK (Python) | Voice cloning ile |
| Video kompozisyon | `remotion` + `@remotion/cli` (Node) | React bileşenleri ile katmanlı video |
| Video preview | `npx remotion studio` | Tarayıcıda gerçek zamanlı önizleme |
| Video render | `npx remotion render` (CLI) | Python subprocess ile çağrılır |
| Video doğrulama | `ffprobe` (binary CLI) | Sadece binary, Python paketi gerekmez |
| Klasör izleme | `watchdog` (Python) | PDF hook için |
| Zamanlayıcı | `APScheduler` (Python) | Cron-like zamanlama |
| Drive upload | Google Drive MCP | Zaten bağlı ✅ |
| Config | `python-dotenv` + `PyYAML` | .env ve config.yaml |
| Logging | `loguru` | Temiz log çıktısı |

---

## ⚡ Hızlı Başlangıç Sırası

Claude bu projeyi sırayla build ederken şu sırayı takip et:

1. `script_generator.py` → test et → ✅
2. `tts_engine.py` → test et → ✅
3. `remotion/src/Root.tsx` + `ShortVideo.tsx` iskelet → studio'da aç → ✅
4. `ParkourBackground.tsx` → `CharacterOverlay.tsx` → `SubtitleLayer.tsx` → ✅
5. `video_renderer.py` (Python subprocess → Remotion CLI) → test et → ✅
6. `quality_checker.py` → ✅
7. `drive_uploader.py` → ✅
8. `main.py` → uçtan uca test → ✅
9. `hooks/` → aktive et → ✅

**Bir skill bitmeden diğerine geçme. Her skill'i bağımsız test et.**

---

## 🚨 Bilinen Riskler & Çözümler

| Risk | Çözüm |
|---|---|
| ElevenLabs'ta Rick/Morty sesi yok | Voice design özelliği ile benzer ses oluştur; alternatif: `Coqui TTS` lokal model |
| Remotion render yavaş | `--concurrency 4` flag'i, M1/M2 Mac veya güçlü CPU'da çok daha hızlı |
| `staticFile()` path hatası | Tüm asset'lerin `remotion/public/` altında olduğunu kontrol et |
| Video süresi tutmuyor | `durationInFrames`'i props'tan hesapla: `Math.round(totalDurationSec * 30)` |
| Karakter PNG pozisyonu bozuk | `AbsoluteFill` içinde `position: absolute`, `bottom: 0` kullan |
| Drive upload yavaş | Remotion default ~8Mbps, `--video-bitrate 4M` ile düşür |
| PDF'den anlamsız metin çıkıyor | İlk 2000 karakteri Claude'a gönder, "ana konuyu bul" de |

---

## 📝 Claude'a Kodlama Sırasında Verilecek Talimatlar

Her skill yazılırken Claude'a söyle:

> "Bu projeyi CLAUDE.md'deki plana göre build ediyoruz. Şu an [SKILL ADI] üzerinde çalışıyoruz. Modüler yaz, test fonksiyonları ekle, hata mesajları açıklayıcı olsun. `loguru` ile loglama yap. Hazır olunca terminal'de test edilebilecek bir `if __name__ == '__main__'` bloğu ekle."
