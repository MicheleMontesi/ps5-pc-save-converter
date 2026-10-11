"""
Central game converter registry.
Allows dynamic registration and auto-detection of game modules.
"""

import os
import zipfile
import io
from typing import Dict, List, Optional, Any
from .base import BaseGameConverter


class GameRegistry:
    """Singleton-style registry for all supported game converters."""
    _converters: Dict[str, BaseGameConverter] = {}
    _title_id_map: Dict[str, str] = {}

    @classmethod
    def register(cls, converter: BaseGameConverter) -> None:
        """Registers a game converter plugin."""
        cls._converters[converter.game_id] = converter
        for tid in converter.title_ids:
            cls._title_id_map[tid.upper()] = converter.game_id

    @classmethod
    def get(cls, game_id: str) -> Optional[BaseGameConverter]:
        """Gets a converter by game_id."""
        return cls._converters.get(game_id)

    @classmethod
    def list_games(cls) -> List[Dict[str, Any]]:
        """Returns metadata for all registered games for UI rendering."""
        games = []
        for g_id, conv in cls._converters.items():
            games.append({
                'id': conv.game_id,
                'name': conv.display_name,
                'title_ids': conv.title_ids,
                'format': conv.format_description,
                'active': conv.is_active
            })
        return games

    @classmethod
    def detect_game_from_source(cls, input_source: Any) -> Optional[str]:
        """
        Attempts to detect which game an archive or path belongs to
        by inspecting Title IDs (e.g. PPSA01603) or specific filenames.
        """
        # If string or path-like
        if isinstance(input_source, (str, os.PathLike)):
            path_str = str(input_source).upper()
            # Direct check in path or filename (e.g. PPSA01603_saves_dec.zip)
            for tid, g_id in cls._title_id_map.items():
                if tid in path_str:
                    return g_id

            if os.path.isdir(input_source):
                for root, dirs, files in os.walk(input_source):
                    for d in dirs:
                        if d.upper() in cls._title_id_map:
                            return cls._title_id_map[d.upper()]
                    for f in files:
                        for tid, g_id in cls._title_id_map.items():
                            if tid in f.upper():
                                return g_id

        # If ZIP file or byte stream
        zf = None
        if isinstance(input_source, (str, os.PathLike)) and str(input_source).lower().endswith('.zip'):
            try:
                zf = zipfile.ZipFile(input_source)
            except Exception:
                zf = None
        elif hasattr(input_source, 'read'):
            pos = input_source.tell() if hasattr(input_source, 'tell') else None
            try:
                zf = zipfile.ZipFile(input_source)
            except Exception:
                zf = None
            if pos is not None and hasattr(input_source, 'seek'):
                input_source.seek(pos)

        if zf:
            try:
                for name in zf.namelist():
                    name_upper = name.upper()
                    for tid, g_id in cls._title_id_map.items():
                        if tid in name_upper:
                            return g_id
            except Exception:
                pass

        return None
