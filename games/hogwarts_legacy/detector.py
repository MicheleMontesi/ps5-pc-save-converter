"""
Save directory detector for Hogwarts Legacy across Windows, macOS, and Linux.
"""

import os
import sys
import glob
from pathlib import Path
from typing import List, Dict, Any


def find_hogwarts_save_directories() -> List[Dict[str, Any]]:
    """
    Scans the system for Hogwarts Legacy save directories.
    Returns a list of dicts with path, platform, user_id, and existing saves count.
    """
    candidates = []

    if sys.platform == 'win32':
        local_app_data = os.environ.get('LOCALAPPDATA')
        if local_app_data:
            base_path = Path(local_app_data) / "Hogwarts Legacy" / "Saved" / "SaveGames"
            if base_path.exists():
                for user_dir in base_path.iterdir():
                    if user_dir.is_dir() and not user_dir.name.startswith('.'):
                        candidates.append({
                            'path': str(user_dir),
                            'platform': 'Windows',
                            'user_id': user_dir.name,
                            'type': 'Native Windows'
                        })

    elif sys.platform == 'darwin':
        # macOS: Search Whisky, CrossOver, Heroic, PortingKit
        home = Path.home()
        search_patterns = [
            home / "Library" / "Application Support" / "com.isaacmarovitz.Whisky" / "Bottles" / "*" / "drive_c" / "users" / "*" / "AppData" / "Local" / "Hogwarts Legacy" / "Saved" / "SaveGames",
            home / "Library" / "Application Support" / "CrossOver" / "Bottles" / "*" / "drive_c" / "users" / "*" / "AppData" / "Local" / "Hogwarts Legacy" / "Saved" / "SaveGames",
            home / "Games" / "Heroic" / "Prefixes" / "*" / "drive_c" / "users" / "*" / "AppData" / "Local" / "Hogwarts Legacy" / "Saved" / "SaveGames",
            home / ".wine" / "drive_c" / "users" / "*" / "AppData" / "Local" / "Hogwarts Legacy" / "Saved" / "SaveGames",
        ]

        for pattern in search_patterns:
            for save_games_path in glob.glob(str(pattern)):
                p = Path(save_games_path)
                if p.is_dir():
                    for user_dir in p.iterdir():
                        if user_dir.is_dir() and not user_dir.name.startswith('.'):
                            bottle_name = "Unknown Bottle"
                            parts = user_dir.parts
                            if "Whisky" in parts and "Bottles" in parts:
                                b_idx = parts.index("Bottles")
                                bottle_name = f"Whisky ({parts[b_idx + 1]})"
                            elif "CrossOver" in parts and "Bottles" in parts:
                                b_idx = parts.index("Bottles")
                                bottle_name = f"CrossOver ({parts[b_idx + 1]})"

                            candidates.append({
                                'path': str(user_dir),
                                'platform': 'macOS (Wine)',
                                'user_id': user_dir.name,
                                'type': bottle_name
                            })

    elif sys.platform.startswith('linux'):
        # Linux / Steam Deck: Proton appid 990080
        home = Path.home()
        search_patterns = [
            home / ".local" / "share" / "Steam" / "steamapps" / "compatdata" / "990080" / "pfx" / "drive_c" / "users" / "steamuser" / "AppData" / "Local" / "Hogwarts Legacy" / "Saved" / "SaveGames",
            home / ".steam" / "steam" / "steamapps" / "compatdata" / "990080" / "pfx" / "drive_c" / "users" / "steamuser" / "AppData" / "Local" / "Hogwarts Legacy" / "Saved" / "SaveGames",
        ]
        for pattern in search_patterns:
            for save_games_path in glob.glob(str(pattern)):
                p = Path(save_games_path)
                if p.is_dir():
                    for user_dir in p.iterdir():
                        if user_dir.is_dir() and not user_dir.name.startswith('.'):
                            candidates.append({
                                'path': str(user_dir),
                                'platform': 'Linux / Steam Deck',
                                'user_id': user_dir.name,
                                'type': 'Proton (Steam)'
                            })

    for c in candidates:
        p = Path(c['path'])
        sav_files = list(p.glob("*.sav"))
        c['existing_saves_count'] = len(sav_files)
        c['has_savegamelist'] = (p / "SaveGameList.sav").exists()
        c['existing_files'] = [f.name for f in sav_files]

    return candidates
