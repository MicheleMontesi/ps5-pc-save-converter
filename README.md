# PS5 ⇄ PC Save Converter 🎮 ⇄ 💻

[![Platform](https://img.shields.io/badge/Platforms-PS5%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](#)
[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Plugin%20System-purple.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A modular, extensible Web Application and framework for **bidirectional save conversion between PlayStation 5 (PS5) and PC**.

Built as a **generic multi-game cross-save framework**, it features a pluggable architecture allowing new games to be added with minimal code, while shipping with **Hogwarts Legacy** as its first fully featured, battle-tested reference module.

---

## 📑 Table of Contents

- [🎮 Supported Titles](#supported-titles)
- [🌟 Key Features](#key-features)
- [⚡ Quick Start](#quick-start)
  - [macOS and Linux](#macos-and-linux)
  - [Windows](#windows)
  - [Manual Setup](#manual-setup)
- [📖 How It Works](#how-it-works)
  - [From PS5 to PC](#from-ps5-to-pc)
  - [From PC to PS5](#from-pc-to-ps5)
- [🏗️ Architecture and Directory Structure](#architecture-and-directory-structure)
- [🧩 Adding a New Game Module](#adding-a-new-game-module)
- [🤝 Contributing](#contributing)
  - [How You Can Help](#how-you-can-help)
- [🗺️ Roadmap](#roadmap)
- [⚖️ Disclaimer](#disclaimer)
- [📄 License](#license)

---

## 🎮 Supported Titles

The table below lists all officially registered game modules and their current support status:

| Game | PlayStation Title IDs | PS5 Save Engine | PC Target Format | Status | Module Path |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Hogwarts Legacy** | `PPSA01603` (EU)<br>`PPSA01602` (NA)<br>`CUSA12824` (PS4) | Unreal Engine 4 GVAS<br>+ Oodle Kraken (`0x9e2a83c1`)<br>+ SQLite DB | Steam / Epic / GOG<br>(`HL-00-*.sav`, `SaveGameList.sav`) | 🟢 **Supported & Tested** | [`games/hogwarts_legacy/`](games/hogwarts_legacy/) |
| **Elden Ring** | `PPSA03365`, `PPSA03366` | Proprietary BND4 / Sl2 | Steam (`ER0000.sl2`) | 🟡 *Planned / Help Wanted* | Template in `CONTRIBUTING.md` |
| **Cyberpunk 2077** | `PPSA03974`, `PPSA03975` | REDengine (`sav.dat`) | Steam / GOG / Epic | 🟡 *Planned / Help Wanted* | — |
| **Your Favorite Game** | Any Garlic-dumped PS5 title | Any container | Any PC save format | 💡 **Open for PRs!** | See [Contributing](#contributing) |

> 💡 **Automatic Detection**: When uploading decrypted ZIP archives exported from **Garlic Save Manager**, the converter automatically inspects the folder hierarchy and Title IDs to select the matching game module without requiring manual selection.

---

## 🌟 Key Features

* 🧩 **Pluggable Modular Engine:**
  * Clean separation of concerns via [`core.base.BaseGameConverter`](core/base.py).
  * Central [`GameRegistry`](core/registry.py) that handles dynamic game registration, auto-detection from PS5 Title IDs, and API discovery.
* 🔁 **Bidirectional Conversion (PS5 ⇄ PC):**
  * **PS5 ➔ PC:** Ingests decrypted saves exported from **Garlic Save Manager**, patches container platform headers (`PS5` ➔ `Windows`), maps internal slot indices, and preserves native compression bit-for-bit.
  * **PC ➔ PS5:** Packages PC `.sav` files into Garlic Save Manager's expected directory layout (`PPSAxxxxx/sdimg_xxxx/ue4savegame.ps5.sav`), patches platform headers (`Windows` ➔ `PS5`), ready for instant console import, re-encryption, and resigning.
* 🧙 **Active Reference Module: Hogwarts Legacy:**
  * **Oodle Kraken Chunk Preservation**: Preserves chunk-compressed SQLite blobs (`0x9e2a83c1`), ensuring 100% compatibility with modern PC game updates and community save editors.
  * **Real-time Character Introspection**: Extracts character name, Hogwarts House (with crests), wand details (wood, core, length, flexibility), XP, talent/perk points, and inventory capacity directly from memory.
  * **Automatic Menu Indexing**: Restores `SaveGameList.sav` to ensure your character immediately appears in the main menu.
* 📂 **Cross-Platform Directory Auto-Detection:**
  * **Windows:** Automatically finds `%LOCALAPPDATA%\...\SaveGames\<SteamID>\`.
  * **macOS:** Scans Wine prefixes across **Whisky**, **CrossOver**, and **Heroic Games Launcher**.
  * **Linux / Steam Deck:** Scans Valve Proton `compatdata` directories.
* 🛡️ **Automated Safety Backups:**
  * Creates timestamped backups (`Backup_YYYYMMDD_HHMMSS/`) of target directories prior to installing new saves.
* 🌐 **Zero-Config LAN Web UI:**
  * Wizarding dark theme with modern glassmorphism.
  * Accessible from any device on your local network (e.g. run on Mac, access from Windows PC or Steam Deck).

---

## ⚡ Quick Start

### macOS and Linux
```bash
git clone https://github.com/MicheleMontesi/ps5-pc-save-converter.git
cd ps5-pc-save-converter
./start.sh
```
*(Automatically creates a Python virtual environment, installs dependencies, and opens the Web UI at `http://127.0.0.1:5050`)*

### Windows
1. Clone or download this repository.
2. Double-click **`start.bat`**.
*(Requires Python 3.10+ installed with "Add Python to PATH" checked)*

### Manual Setup
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

---

## 📖 How It Works

### From PS5 to PC
```
[Jailbroken PS5]
       │
       ▼  Garlic Save Manager (Export Decrypted Save)
[PPSA01603_saves_dec.zip]
       │
       ▼  Drag & Drop into Web UI
[PS5 ⇄ PC Save Converter] ➔ Auto-detects Title ID + Patches GVAS Platform Headers
       │
       ├── Option A: "Install Directly to Game Folder" (Auto-backup + local PC copy)
       └── Option B: "Download ZIP Archive" (Ready-to-use PC saves)
```

1. On your jailbroken PS5, open **Garlic Save Manager** (`http://<ps5-ip>:8082`).
2. Export the decrypted save (e.g., `PPSA01603_saves_dec.zip`).
3. Open the Web UI and drag the ZIP file into the dropzone.
4. The system **auto-detects the game**, loads character metadata, and verifies save integrity.
5. Click **"Install Directly to Game Folder"** (if running locally on PC) or **"Download ZIP Archive"** to get your PC-ready saves.

### From PC to PS5
```
[PC Save Files] (e.g., HL-00-00.sav)
       │
       ▼  Drag & Drop into Web UI (Mode: PC to PS5)
[PS5 ⇄ PC Save Converter] ➔ Patches Platform Headers + Packages Garlic Directory Layout
       │
       ▼  "Download Package for Garlic Save Manager"
[PPSA01603_Garlic_Ready.zip]
       │
       ▼  Garlic Save Manager (Import Decrypted Save)
[PS5 Re-encrypter / Keystone Resigner]
       │
       ▼
[Play on PS5 Console!]
```

1. In the Web UI, toggle **"From PC to PS5"** (💻 ➔ 🎮).
2. Drag your PC save files (or a ZIP file containing them).
3. Click **"Download Package for Garlic Save Manager (PS5)"**.
4. In Garlic Save Manager on your PS5, import the generated ZIP to re-encrypt and resign the save back to your console account.

---

## 🏗️ Architecture and Directory Structure

```text
ps5-pc-save-converter/
├── core/                                # Generic Framework Engine
│   ├── base.py                          # BaseGameConverter abstract interface
│   ├── registry.py                      # Dynamic plugin registry & Title ID matcher
│   ├── installer.py                     # Safe backup engine & file installer
│   └── __init__.py
├── games/                               # Pluggable Game Modules
│   ├── hogwarts_legacy/                 # Active Module: Hogwarts Legacy
│   │   ├── converter.py                 # UE4 GVAS patcher + Oodle chunk preserver
│   │   ├── detector.py                  # Windows, macOS Whisky/Wine, Proton scanner
│   │   └── __init__.py                  # HogwartsLegacyConverter implementation
│   └── __init__.py                      # Auto-registers game plugins
├── app.py                               # Flask server & REST API
├── templates/
│   └── index.html                       # Responsive Web UI
├── static/
│   ├── css/style.css                    # Glassmorphism dark theme
│   └── js/app.js                        # Dynamic frontend (API-driven game loader)
├── start.sh                             # macOS/Linux one-click launcher
├── start.bat                            # Windows one-click launcher
├── CONTRIBUTING.md                      # Guide for adding new game converters
└── LICENSE                              # MIT License
```

---

## 🧩 Adding a New Game Module

Adding support for another PS5 title is as simple as creating a subclass of `BaseGameConverter`:

```python
from typing import Dict, Any, List
from core.base import BaseGameConverter
from core.registry import GameRegistry

class EldenRingConverter(BaseGameConverter):
    @property
    def game_id(self) -> str:
        return 'elden-ring'

    @property
    def display_name(self) -> str:
        return 'Elden Ring'

    @property
    def title_ids(self) -> List[str]:
        # PS5 Title IDs for auto-detection
        return ['PPSA03365', 'PPSA03366']

    @property
    def format_description(self) -> str:
        return 'Proprietary BND4 / Raw Sl2'

    def convert_ps5_to_pc(self, input_source: Any) -> Dict[str, Any]:
        # Parse decrypted PS5 save, patch headers/checksums, return PC files
        saves = {'ER0000.sl2': b'...'}
        character_info = {'name': 'Tarnished', 'level': 150}
        return {'character': character_info, 'saves': saves, 'errors': []}

    def convert_pc_to_ps5(self, input_source: Any) -> Dict[str, Any]:
        # Convert PC file back to Garlic decrypted format
        saves = {'PPSA03365/sdimg_savedata/savedata.sav': b'...'}
        return {'character': None, 'saves': saves, 'errors': []}

    def find_candidate_save_directories(self) -> List[Dict[str, Any]]:
        # Locate game saves on Windows, Proton, or macOS Wine
        return [{'path': 'C:\\Users\\...\\AppData\\Roaming\\EldenRing\\...', 'platform': 'Windows'}]

# Register in games/__init__.py
GameRegistry.register(EldenRingConverter())
```

Once registered, the game will automatically appear in the UI, match Garlic ZIP uploads by Title ID, and support safe backups and installation.

---

## 🤝 Contributing

Contributions are warmly welcomed! We are actively looking for contributors to help expand game support, test saves, and enhance platform detection.

### How You Can Help
1. **Implement New Game Modules**: Pick a title from the [Supported Titles](#supported-titles) table or request a new one.
2. **Provide Save Dumps**: Share decrypted PS5 saves (exported via Garlic Save Manager) alongside matching PC saves for reverse engineering container formats.
3. **Bug Reports & Feedback**: Submit issues on GitHub for path detection failures or formatting incompatibilities.

For full developer instructions, workflow guidelines, and code conventions, please see [**CONTRIBUTING.md**](CONTRIBUTING.md).

---

## 🗺️ Roadmap

- [x] Bidirectional save converter for Hogwarts Legacy (PS5 ⇄ PC)
- [x] Oodle Kraken chunk compression preservation
- [x] Modular plugin architecture & auto-detection engine
- [x] Cross-platform save path scanner (Windows, macOS Wine/Whisky, Steam Deck Proton)
- [ ] Add converter module for **Elden Ring** (`PPSA03365`)
- [ ] Add converter module for **Cyberpunk 2077** (`PPSA03974`)
- [ ] CLI mode for headless and batch conversions
- [ ] Standalone executable bundle (PyInstaller) for zero-dependency Windows execution

---

## ⚖️ Disclaimer

This tool is an unofficial, community-developed open-source project. It is not affiliated with, endorsed by, or associated with Sony Interactive Entertainment, Warner Bros. Games, Avalanche Software, or any other game publisher. Always create backups of your save files prior to modification.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
