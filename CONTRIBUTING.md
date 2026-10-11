# Contributing to PS5 ⇄ PC Save Converter

First off, thank you for considering contributing to **PS5 ⇄ PC Save Converter**! 🎉

This project is built as an open, community-driven framework designed to make cross-platform save transfers accessible for multiple PlayStation 5 titles. Whether you are adding support for a new game, improving an existing converter, testing saves, or refining documentation, your contributions are welcome.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How You Can Contribute](#how-you-can-contribute)
  - [1. Add a New Game Module](#1-add-a-new-game-module)
  - [2. Provide Save Dumps for Testing](#2-provide-save-dumps-for-testing)
  - [3. Report Bugs & Request Features](#3-report-bugs--request-features)
- [Development Setup](#development-setup)
- [Creating a New Game Converter](#creating-a-new-game-converter)
- [Pull Request Guidelines](#pull-request-guidelines)

---

## Code of Conduct

Please be respectful, constructive, and helpful when interacting with fellow contributors and users in discussions, issues, and pull requests.

---

## How You Can Contribute

### 1. Add a New Game Module
The framework is completely modular. Game converters live inside the `games/` directory as self-contained plugins inheriting from `BaseGameConverter`. If you know the save file format, header structures, or compression algorithms for a PS5 title, you can implement a module and submit a PR!

### 2. Provide Save Dumps for Testing
To build support for a new game, developers need decrypted PS5 save dumps (obtained via **Garlic Save Manager** on a jailbroken PS5) and corresponding PC saves to compare headers and container formats.
> ⚠️ **Note**: Remove any personal account credentials or sensitive tokens from save files before sharing.

### 3. Report Bugs & Request Features
Found a save that fails to convert, a save editor incompatibility, or a platform path that wasn't auto-detected? Open an issue on GitHub with:
- The game title and PlayStation Title ID (e.g., `PPSA01603`).
- Your platform (Windows, macOS Whisky/CrossOver, Linux Proton).
- Error messages or console logs.

---

## Development Setup

1. **Fork and clone** the repository:
   ```bash
   git clone https://github.com/<your-username>/ps5-pc-save-converter.git
   cd ps5-pc-save-converter
   ```

2. **Set up Python virtual environment** (Python 3.10+ recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the local development server**:
   ```bash
   python3 app.py
   ```
   The Web UI will be accessible at `http://127.0.0.1:5050`.

---

## Creating a New Game Converter

Every game module inherits from [`core.base.BaseGameConverter`](core/base.py) and is placed in `games/<your_game_id>/`:

### Module Structure
```text
games/
└── my_game/
    ├── __init__.py      # Converter class implementation
    ├── converter.py     # Binary parsing, header patcher, compression
    └── detector.py      # Cross-platform PC save path scanner
```

### Implementing `BaseGameConverter`

```python
from typing import Dict, Any, List
from core.base import BaseGameConverter

class MyGameConverter(BaseGameConverter):
    @property
    def game_id(self) -> str:
        """Unique slug identifier, e.g. 'elden-ring'"""
        return 'my-game'

    @property
    def display_name(self) -> str:
        """Human-readable title displayed in the Web UI"""
        return 'My Game Title'

    @property
    def title_ids(self) -> List[str]:
        """PS5 Title IDs used for automatic ZIP/folder detection"""
        return ['PPSA12345', 'CUSA12345']

    @property
    def format_description(self) -> str:
        """Displayed on the format badge in the UI"""
        return 'Custom Container + Zlib Compression'

    def convert_ps5_to_pc(self, input_source: Any) -> Dict[str, Any]:
        """
        Converts decrypted PS5 saves to PC files.
        Must return:
        {
            'character': dict or None,  # (optional) metadata for preview
            'saves': {'save_file.sav': b'...'},
            'errors': []
        }
        """
        ...

    def convert_pc_to_ps5(self, input_source: Any) -> Dict[str, Any]:
        """
        Converts PC files to Garlic Save Manager directory structure:
        PPSA12345/sdimg_xxxx/ue4savegame.ps5.sav
        """
        ...

    def find_candidate_save_directories(self) -> List[Dict[str, Any]]:
        """
        Scans Windows %LOCALAPPDATA% / %APPDATA%, macOS Wine/Whisky, and Linux Proton
        for the game's PC save directory.
        """
        ...
```

### Registering the Converter
In `games/__init__.py`:
```python
from core.registry import GameRegistry
from .my_game import MyGameConverter

GameRegistry.register(MyGameConverter())
```

Once registered, the Web UI will automatically include your game in the selector, match Title IDs from Garlic ZIPs, and handle safe installations and backups.

---

## Pull Request Guidelines

1. **Branch Naming**: Use descriptive branches like `feat/elden-ring-converter` or `fix/steam-proton-detection`.
2. **Commit Messages**: Follow conventional commits (e.g., `feat(games): add Elden Ring converter module`, `fix(ui): resolve drag-and-drop file input reset`).
3. **Testing**: Verify that bidirectional conversions work and produce playable saves on both PC and console.
4. **Documentation**: If adding a new game, update the **Supported Titles** table in `README.md`.
