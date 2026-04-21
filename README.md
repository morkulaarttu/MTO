# MTO — Mp3ToOgg

<div align="center">

<img src="logoMTO.png" width="120" alt="MTO Logo"/>

**A modern audio converter and YouTube downloader built for My Winter Car.**

[![Version](https://img.shields.io/badge/version-1.0.2--beta-7b68ee?style=flat-square)](https://github.com/MorkulaArttu/MTO/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-0078d4?style=flat-square)](https://github.com/MorkulaArttu/MTO/releases)
[![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red?style=flat-square)](#license)

</div>

---

## What is MTO?

MTO (Mp3ToOgg) is a free desktop tool that converts MP3 audio files to OGG format — built specifically for *My Winter Car* players who want custom radio tracks in the game.

Point it at a folder of MP3s, set your My Winter Car Radio directory as the destination, and MTO handles everything automatically — naming files `track1.ogg`, `track2.ogg` and so on, always picking the next free number without overwriting anything.

It also includes a built-in YouTube downloader that pulls audio directly into OGG format, ready to drop straight into the game.

---

## Features

- **MP3 → OGG conversion** with automatic track numbering
- **Source / Destination split** — convert from anywhere, save directly to My Winter Car Radio
- **Auto-detects My Winter Car** via Steam library scan
- **YouTube downloader** — paste a link, get a track file
- **Download queue** — add multiple links and let it run
- **Video preview** before downloading
- **Conversion history** log
- **Select & reorder** files before converting — checkboxes and ↑↓ buttons
- **Windows notifications** when jobs finish
- **Dark & light theme** with accent color picker
- **9 languages** — English, Finnish, Swedish, German, French, Spanish, Chinese, Japanese, Korean
- **Minimize to system tray**
- **No manual setup** — FFmpeg and yt-dlp install automatically on first launch

---

## Download

Get the latest release from the [Releases page](https://github.com/MorkulaArttu/MTO/releases).

Download `MTO.exe` — no installation required, just run it.

> **First launch:** MTO will automatically download FFmpeg (~70 MB) and yt-dlp (~10 MB) from GitHub. This only happens once.

---

## Requirements

- Windows 10 or 11
- Internet connection (first launch only, for FFmpeg + yt-dlp)
- My Winter Car on Steam (for auto-detection — optional)

---

## Usage

### Converting MP3s

1. Under **SOURCE**, select the folder containing your MP3 files
2. Under **DESTINATION**, MTO auto-fills your My Winter Car Radio folder — or select it manually
3. Choose which files to convert using the checkboxes
4. Reorder with ↑↓ if needed
5. Press **Start Conversion**

### Downloading from YouTube

1. Go to the **YouTube** tab
2. Paste a video or playlist URL
3. Press **Fetch Info** to preview before downloading
4. Press **+ Add to Queue** to queue multiple links
5. Select your destination folder
6. Press **Download**

---

## Building from Source

```bash
pip install customtkinter pystray pillow
python -m PyInstaller --onefile --windowed --name "MTO" --icon "logo.ico" --clean app.py
```

Place `logo.ico` in the same folder as `app.py` before building.

---

## License

Copyright © 2025 @MorkulaArttu. All rights reserved.

This software is free to use but may not be modified, redistributed, or repackaged without explicit written permission from the author.

See [LICENSE](LICENSE) for full terms.

---

<div align="center">
Made by <a href="https://github.com/MorkulaArttu">@MorkulaArttu</a>
</div>
