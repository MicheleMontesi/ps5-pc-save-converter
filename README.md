# PS5 ⇄ PC Save Converter 🎮 ⇄ 💻

[![Platform](https://img.shields.io/badge/Platforms-PS5%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](#)
[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Plugin%20System-purple.svg)](#)
[![Active Module](https://img.shields.io/badge/Active%20Module-Hogwarts%20Legacy-gold.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](#)

A modular, extensible Web Application and framework for **bidirectional save conversion between PlayStation 5 (PS5) and PC**.

Designed as a **generic multi-game framework**, it features a pluggable architecture allowing new games to be added with minimal code, while shipping with **Hogwarts Legacy** as its first fully featured, active reference implementation.

> **Italiano**: Un convertitore di salvataggi modulare ed estensibile tra **PlayStation 5 (Garlic Save Manager)** e **PC (Windows / Steam / Epic Games / macOS Whisky / Steam Deck Proton)**. Progettato come framework generico per supportare più giochi tramite plugin: include **Hogwarts Legacy** come primo modulo attivo e funzionante.

---

## 🌟 Key Features / Caratteristiche

* 🧩 **Modular Plugin Architecture:**
  * Clean abstraction layer (`core.base.BaseGameConverter`) decoupling game-specific save logic from the Web UI, filesystem scanner, and installation manager.
  * Central `GameRegistry` with **automatic game detection** from PS5 Title IDs (e.g. `PPSA01603`) in ZIP archives or folder trees.
* 🔁 **Bidirectional Conversion (PS5 ⇄ PC):**
  * **PS5 ➔ PC:** Ingests decrypted saves exported from **Garlic Save Manager**, patches container platform headers, translates internal slot schemes, and preserves native compression (e.g. Oodle Kraken chunk compression).
  * **PC ➔ PS5:** Packages PC `.sav` files into Garlic Save Manager's expected directory layout (`PPSAxxxxx/sdimg_xxxx/ue4savegame.ps5.sav`), ready for instant console import, re-encryption, and resigning.
* 🧙 **Active Module: Hogwarts Legacy:**
  * Bit-for-bit **Oodle Kraken chunk compression** (`0x9e2a83c1`) preservation compatible with modern PC patches and Save Editors.
  * Real-time character metadata introspection from in-memory SQLite (House crests, Wand wood/core/length, XP, Perk points, Inventory).
  * Main menu slot index generation (`SaveGameList.sav`).
* 📂 **Cross-Platform Directory Auto-Detection:**
  * **Windows:** Scans `%LOCALAPPDATA%` and game save subdirectories.
  * **macOS:** Scans Wine prefixes across **Whisky**, **CrossOver**, and **Heroic Games Launcher**.
  * **Linux / Steam Deck:** Scans Valve Proton compatdata prefixes.
* 🛡️ **Automated Safety Backups:**
  * Creates timestamped backups (`Backup_YYYYMMDD_HHMMSS/`) of target directories before writing new files.
* 🌐 **Zero-Config LAN Web UI:**
  * Clean glassmorphism interface with drag-and-drop support.
  * Accessible from any device on your local network (e.g. run on Mac, access from Windows PC or Steam Deck).

---

## ⚡ Quick Start / Come Avviare

### macOS & Linux
```bash
git clone https://github.com/MicheleMontesi/ps5-pc-save-converter.git
cd ps5-pc-save-converter
./start.sh
```
*(Automatically creates Python virtual environment, installs dependencies, and opens the Web UI at `http://127.0.0.1:5050`)*

### Windows
1. Clone or download the repository.
2. Double-click **`start.bat`**.
*(Requires Python installed with "Add Python to PATH" enabled)*

---

## 📖 Usage Guide / Guida all'Uso

### 🎮 ➔ 💻 From PS5 to PC:
1. On your jailbroken PS5, open **Garlic Save Manager** (`http://<PS5_IP>:8082`).
2. Export the decrypted save (e.g. `PPSA01603_saves_dec.zip` for Hogwarts Legacy).
3. Open the Web UI and drag the ZIP file into the dropzone.
4. The system will **auto-detect the game** and display character/save details.
5. Click **"Installa Direttamente nella Cartella di Gioco"** (if on PC) or **"Scarica Archivio ZIP"** to download the converted PC files.

### 💻 ➔ 🎮 From PC to PS5:
1. In the Web UI, toggle **"Da PC a PS5"**.
2. Drag your PC save files (or a ZIP archive containing them).
3. Click **"Scarica Pacchetto per Garlic Save Manager (PS5)"**.
4. In Garlic Save Manager on your PS5, import the generated ZIP to re-encrypt and resign the save.

---

## 🏗️ Project Architecture / Architettura del Progetto

```text
ps5-pc-save-converter/
├── core/                                # Generic Framework Core
│   ├── base.py                          # BaseGameConverter abstract interface
│   ├── registry.py                      # Dynamic plugin registry & Title ID detector
│   ├── installer.py                     # Universal backup engine & file installer
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
│   ├── css/style.css                    # Dark wizarding glassmorphism theme
│   └── js/app.js                        # Dynamic frontend (API-driven game loader)
├── start.sh                             # macOS/Linux launcher
└── start.bat                            # Windows launcher
```

---

## 🧩 Adding a New Game Module / Come Aggiungere un Nuovo Gioco

The converter is engineered to make adding new games straightforward. To implement a new game module:

### 1. Create a module folder in `games/`
Create `games/<your_game_name>/__init__.py`.

### 2. Subclass `BaseGameConverter`
Inherit from `core.base.BaseGameConverter` and implement the required properties and methods:

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
        # Parse decrypted PS5 save, convert headers/checksums, return PC files
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
```

### 3. Register your module in `games/__init__.py`
```python
from core.registry import GameRegistry
from .hogwarts_legacy import HogwartsLegacyConverter
from .elden_ring import EldenRingConverter

GameRegistry.register(HogwartsLegacyConverter())
GameRegistry.register(EldenRingConverter())
```

Once registered:
* The game **instantly appears** in the Web UI game selector.
* Garlic ZIP uploads matching `PPSA03365` or `PPSA03366` will be **automatically identified**.
* Safe backups and directory installation work **out of the box**.

---

## ⚖️ Disclaimer

This tool is an unofficial community open-source project and is not affiliated with, endorsed by, or associated with Sony Interactive Entertainment, Warner Bros. Games, Avalanche Software, or any other game publisher. Always create backups of your save files prior to modification.
