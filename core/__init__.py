"""
Core module for PS5 <-> PC Cross-Save Converter.
Provides base classes, dynamic registry, and file installation utilities.
"""

from .base import BaseGameConverter
from .registry import GameRegistry
from .installer import backup_and_install_saves

__all__ = ['BaseGameConverter', 'GameRegistry', 'backup_and_install_saves']
