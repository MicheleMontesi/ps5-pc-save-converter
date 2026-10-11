# PS5 ⇄ PC Save Converter 🎮 ⇄ 💻

[![Platform](https://img.shields.io/badge/Platforms-PS5%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](#)
[![Game](https://img.shields.io/badge/Game-Hogwarts%20Legacy-gold.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](#)

Web Application with graphical interface for **bidirectional save conversion between PlayStation 5 (PS5) and PC**.
Currently specialized for **Hogwarts Legacy** (designed to support additional titles in the future).

> **Italiano**: Convertitore di salvataggi bidirezionale tra **PlayStation 5 (Garlic Save Manager)** e **PC (Windows / Steam / Epic Games / macOS Whisky / Steam Deck Proton)**.

---

## 🌟 Highlights / Caratteristiche

* 🔁 **Bidirectional Conversion / Conversione Bidirezionale:**
  * **PS5 ➔ PC:** Takes decrypted saves from **Garlic Save Manager** (`PPSA01603`), patches GVAS platform headers (`PS5` ➔ `Windows`), maps internal slots (`HL-00-00.sav` ... `HL-00-14.sav`, `SaveGameList.sav`, `SavedUserOptions.sav`), and preserves **Oodle Kraken chunk compression** required by modern PC game versions and Save Editors.
  * **PC ➔ PS5:** Packages PC `.sav` files into the Garlic Save Manager directory layout (`PPSA01603/sdimg_HLxxxx/ue4savegame.ps5.sav`), patches platform headers (`Windows` ➔ `PS5`), ready for re-encryption and resigning back to PlayStation 5.
* 🧙 **Real-Time Character Preview / Anteprima Personaggio:**
  * Reads the in-memory SQLite database dynamically to display:
    * Character name and surname (e.g. *MichiPino Colapalla*)
    * Hogwarts House (*Ravenclaw, Gryffindor, Slytherin, Hufflepuff*) with colors and crests
    * Complete wand details (*Wood, Core, Length, Flexibility*)
    * Experience points (XP), Talent/Perk points, and Inventory capacity
* 📂 **Automatic Game Directory Detection / Rilevamento Automatico Cartelle:**
  * **Windows:** Auto-detects `%LOCALAPPDATA%\Hogwarts Legacy\Saved\SaveGames\<UserID>\`
  * **macOS:** Scans Whisky, CrossOver, Wine, and Heroic prefixes
  * **Linux / Steam Deck:** Scans Steam Proton prefixes
* 🛡️ **Automated Backups / Backup di Sicurezza:**
  * Automatically creates a timestamped `Backup_YYYYMMDD_HHMMSS/` of your existing saves before applying new ones.
  * Updates `SaveGameList.sav` to ensure your character immediately appears in the game's main menu.
* 🌐 **Cross-Device & LAN Support:**
  * Run the server on your Mac or PC and access it from any browser on your local network (e.g., `http://192.168.x.x:5050`).

---

## ⚡ Quick Start / Come Avviare

### macOS / Linux:
```bash
git clone https://github.com/MicheleMontesi/ps5-pc-save-converter.git
cd ps5-pc-save-converter
./start.sh
```
*(Automatically sets up the virtual environment, installs dependencies, and opens the Web UI in your browser on `http://127.0.0.1:5050`)*

### Windows:
1. Double-click **`start.bat`**.
*(Requires Python installed with "Add Python to PATH" checked. It automatically configures the venv and launches the Web UI)*

---

## 📖 How to Use / Guida all'Uso

### 🎮 ➔ 💻 Da PS5 a PC:
1. On your Jailbroken PS5, open **Garlic Save Manager** (browser at `http://<PS5_IP>:8082`).
2. Export the decrypted save for *Hogwarts Legacy* (`PPSA01603`) as a `.zip` file (e.g. `PPSA01603_saves_dec.zip`).
3. In the Web UI, select **"Da PS5 a PC"** and drag the ZIP file (or select individual `.sav` files).
4. Review the character preview card.
5. Click **"Installa Direttamente nella Cartella di Gioco"** (if running locally on PC) or **"Scarica Archivio ZIP"** to get your ready-to-use PC saves!

### 💻 ➔ 🎮 Da PC a PS5:
1. In the Web UI, select **"Da PC a PS5"**.
2. Drag your PC `.sav` files (e.g. `HL-00-00.sav`, or a `.zip` containing your PC saves).
3. Click **"Scarica Pacchetto per Garlic Save Manager (PS5)"** (`PPSA01603_Garlic_Ready.zip`).
4. On your PS5, use **Garlic Save Manager** to import, re-encrypt, and resign the save back to your console!

---

## 📂 Project Structure / Struttura del Progetto

```text
ps5-pc-save-converter/
├── app.py                     # Flask Web Server & REST API (LAN enabled)
├── converter.py               # Bidirectional GVAS header & Oodle save converter
├── game_detector.py           # Auto-detector for Windows/Mac/Linux save paths & backups
├── requirements.txt           # Dependencies (Flask, pyooz)
├── start.sh                   # 1-click launcher for macOS & Linux
├── start.bat                  # 1-click launcher for Windows
├── templates/
│   └── index.html             # Web UI HTML template
└── static/
    ├── css/style.css          # Wizarding dark theme with glassmorphism
    └── js/app.js              # Interactive frontend (drag & drop, modals)
```

---

## ⚖️ Disclaimer

This tool is an unofficial community project and is not affiliated with, endorsed by, or associated with Warner Bros. Games, Avalanche Software, or Sony Interactive Entertainment. Always make backups of your saves before modifying or overwriting files.
