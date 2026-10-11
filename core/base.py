"""
Abstract base class defining the contract for game-specific save converters.
Any new game plugin must inherit from BaseGameConverter.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseGameConverter(ABC):
    """
    Abstract interface for a game save converter between PS5 (Garlic) and PC.
    """

    @property
    @abstractmethod
    def game_id(self) -> str:
        """Unique slug identifier for the game, e.g. 'hogwarts-legacy'"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable game title, e.g. 'Hogwarts Legacy'"""
        pass

    @property
    @abstractmethod
    def title_ids(self) -> List[str]:
        """PlayStation Title IDs associated with this game, e.g. ['PPSA01603']"""
        pass

    @property
    def format_description(self) -> str:
        """Brief technical description of save format and compression"""
        return "Generic Save Format"

    @property
    def is_active(self) -> bool:
        """Whether this game converter is active and ready for conversion"""
        return True

    @abstractmethod
    def convert_ps5_to_pc(self, input_source: Any) -> Dict[str, Any]:
        """
        Converts decrypted PS5 save data (file path, directory path, or file-like object)
        into native PC save files.

        Returns:
            {
                'character': Dict[str, Any] or None,  # Metadata for UI preview
                'saves': Dict[str, bytes],            # Mapping { 'filename.sav': b'...' }
                'errors': List[str]                   # Warnings or error messages
            }
        """
        pass

    @abstractmethod
    def convert_pc_to_ps5(self, input_source: Any) -> Dict[str, Any]:
        """
        Converts PC save files into Garlic Save Manager decrypted directory layout
        ready for re-encryption and resigning to PS5.

        Returns:
            {
                'character': Dict[str, Any] or None,
                'saves': Dict[str, bytes],  # Mapping { 'PPSAxxxxx/sdimg_.../file.sav': b'...' }
                'errors': List[str]
            }
        """
        pass

    @abstractmethod
    def find_candidate_save_directories(self) -> List[Dict[str, Any]]:
        """
        Scans the local filesystem (Windows, macOS Wine/Whisky, Linux Proton)
        for this game's save directories.
        """
        pass

    def install_saves(self, target_dir: str, new_saves: Dict[str, bytes], do_backup: bool = True) -> Dict[str, Any]:
        """
        Safely backs up existing saves and writes new_saves into target_dir.
        Can be overridden by games needing custom index handling.
        """
        from .installer import backup_and_install_saves
        return backup_and_install_saves(target_dir, new_saves, do_backup=do_backup)
