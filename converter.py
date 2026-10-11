"""
Compatibility wrapper for converter.py.
Delegates to modular core/registry and games/hogwarts_legacy.
"""

from core.registry import GameRegistry
import games  # triggers registration
from games.hogwarts_legacy.converter import (
    patch_ps5_to_pc_sav,
    patch_pc_to_ps5_sav,
    extract_sqlite_from_sav,
    extract_character_metadata,
    PS5_TO_PC_MAP,
    PC_TO_PS5_MAP
)

hl_converter = GameRegistry.get('hogwarts-legacy')

def convert_ps5_to_pc(input_source):
    return hl_converter.convert_ps5_to_pc(input_source)

def convert_pc_to_ps5(input_source, title_id="PPSA01603"):
    return hl_converter.convert_pc_to_ps5(input_source, title_id)

convert_ps5_zip_to_pc = convert_ps5_to_pc
convert_pc_zip_to_ps5 = convert_pc_to_ps5

def process_archive_or_files(input_source, direction='ps5_to_pc'):
    if direction == 'pc_to_ps5':
        return convert_pc_to_ps5(input_source)
    return convert_ps5_to_pc(input_source)
