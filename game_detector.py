"""
Compatibility wrapper for game_detector.py.
Delegates to modular core/installer and games/hogwarts_legacy/detector.
"""

from games.hogwarts_legacy.detector import find_hogwarts_save_directories
from core.installer import backup_and_install_saves, backup_existing_saves

def find_candidate_save_directories():
    return find_hogwarts_save_directories()
