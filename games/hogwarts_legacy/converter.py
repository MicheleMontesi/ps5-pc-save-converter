"""
Hogwarts Legacy specific conversion and patching logic.
Handles UE4 GVAS save files, Oodle Kraken chunk streams, and SQLite database extraction.
"""

import os
import struct
import sqlite3
import tempfile
import zipfile
import io
from typing import Dict, Any, Optional, Tuple, List

try:
    import ooz
except ImportError:
    ooz = None

COMP_MAGIC = b'\xc1\x83*\x9e'
SQLITE_MAGIC = b'SQLite format 3\x00'
RAW_DB_NEEDLE = b'RawDatabaseImage\x00'

PS5_TO_PC_MAP = {
    'sdimg_HL0000': 'HL-00-00.sav',
    'sdimg_HL0001': 'HL-00-01.sav',
    'sdimg_HL0002': 'HL-00-02.sav',
    'sdimg_HL0003': 'HL-00-03.sav',
    'sdimg_HL0004': 'HL-00-04.sav',
    'sdimg_HL0005': 'HL-00-05.sav',
    'sdimg_HL0006': 'HL-00-06.sav',
    'sdimg_HL0007': 'HL-00-07.sav',
    'sdimg_HL0008': 'HL-00-08.sav',
    'sdimg_HL0009': 'HL-00-09.sav',
    'sdimg_HL0010': 'HL-00-10.sav',
    'sdimg_HL0011': 'HL-00-11.sav',
    'sdimg_HL0012': 'HL-00-12.sav',
    'sdimg_HL0013': 'HL-00-13.sav',
    'sdimg_HL0014': 'HL-00-14.sav',
    'sdimg_SaveGameList': 'SaveGameList.sav',
    'sdimg_SavedUserOptions': 'SavedUserOptions.sav',
}

PC_TO_PS5_MAP = {
    'HL-00-00.sav': 'sdimg_HL0000',
    'HL-00-01.sav': 'sdimg_HL0001',
    'HL-00-02.sav': 'sdimg_HL0002',
    'HL-00-03.sav': 'sdimg_HL0003',
    'HL-00-04.sav': 'sdimg_HL0004',
    'HL-00-05.sav': 'sdimg_HL0005',
    'HL-00-06.sav': 'sdimg_HL0006',
    'HL-00-07.sav': 'sdimg_HL0007',
    'HL-00-08.sav': 'sdimg_HL0008',
    'HL-00-09.sav': 'sdimg_HL0009',
    'HL-00-10.sav': 'sdimg_HL0010',
    'HL-00-11.sav': 'sdimg_HL0011',
    'HL-00-12.sav': 'sdimg_HL0012',
    'HL-00-13.sav': 'sdimg_HL0013',
    'HL-00-14.sav': 'sdimg_HL0014',
    'SaveGameList.sav': 'sdimg_SaveGameList',
    'SavedUserOptions.sav': 'sdimg_SavedUserOptions',
    'HL0000.sav': 'sdimg_HL0000',
    'HL0010.sav': 'sdimg_HL0010',
}

PS5_PLATFORM_BYTES = b'\t\x00\x00\x00Platform\x00\x0c\x00\x00\x00StrProperty\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00PS5\x00'
WIN_PLATFORM_BYTES = b'\t\x00\x00\x00Platform\x00\x0c\x00\x00\x00StrProperty\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00Windows\x00'

PS5_EXCL_PLATFORM_BYTES = b'\x12\x00\x00\x00ExclusivePlatform\x00\x0c\x00\x00\x00StrProperty\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00PS5\x00'
WIN_EXCL_PLATFORM_BYTES = b'\x12\x00\x00\x00ExclusivePlatform\x00\x0c\x00\x00\x00StrProperty\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00Windows\x00'

def patch_ps5_to_pc_sav(data: bytes) -> bytes:
    """Patches PS5 save for PC, changing platform tags to Windows."""
    out = data
    if PS5_PLATFORM_BYTES in out:
        out = out.replace(PS5_PLATFORM_BYTES, WIN_PLATFORM_BYTES, 1)
    if PS5_EXCL_PLATFORM_BYTES in out:
        out = out.replace(PS5_EXCL_PLATFORM_BYTES, WIN_EXCL_PLATFORM_BYTES, 1)
    return out

def patch_pc_to_ps5_sav(data: bytes) -> bytes:
    """Patches PC save for PS5, changing platform tags to PS5."""
    out = data
    if WIN_PLATFORM_BYTES in out:
        out = out.replace(WIN_PLATFORM_BYTES, PS5_PLATFORM_BYTES, 1)
    if WIN_EXCL_PLATFORM_BYTES in out:
        out = out.replace(WIN_EXCL_PLATFORM_BYTES, PS5_EXCL_PLATFORM_BYTES, 1)
    return out

def extract_sqlite_from_sav(data: bytes) -> Optional[bytes]:
    """Extracts raw SQLite database from either an Oodle-compressed or uncompressed save."""
    if RAW_DB_NEEDLE not in data:
        return None

    needle_idx = data.index(RAW_DB_NEEDLE)

    if COMP_MAGIC in data[needle_idx:]:
        if ooz is None:
            raise RuntimeError("The 'pyooz' package is required. Install via: pip install pyooz")

        payload_idx = data.index(COMP_MAGIC, needle_idx)
        head = data[:payload_idx]
        comp_array_len = struct.unpack('<I', head[-4:])[0]
        payload = data[payload_idx : payload_idx + comp_array_len]

        p_off = 0
        decomp_blocks = []
        while p_off < len(payload):
            if p_off + 4 > len(payload):
                break
            magic = struct.unpack('<I', payload[p_off : p_off + 4])[0]
            if magic != 0x9e2a83c1:
                break
            c_size = struct.unpack('<Q', payload[p_off + 16 : p_off + 24])[0]
            u_size = struct.unpack('<Q', payload[p_off + 24 : p_off + 32])[0]
            comp_chunk = payload[p_off + 48 : p_off + 48 + c_size]

            dec = ooz.decompress(comp_chunk, u_size)
            decomp_blocks.append(dec)
            p_off += 48 + c_size

        full_dec = b''.join(decomp_blocks)
        if len(full_dec) > 8:
            cont_size, sqlite_size = struct.unpack('<II', full_dec[:8])
            sqlite_db = full_dec[8 : 8 + sqlite_size]
            if sqlite_db.startswith(SQLITE_MAGIC):
                return sqlite_db

    if SQLITE_MAGIC in data[needle_idx:]:
        sql_idx = data.index(SQLITE_MAGIC, needle_idx)
        page_size = struct.unpack('>H', data[sql_idx + 16 : sql_idx + 18])[0]
        page_count = struct.unpack('>I', data[sql_idx + 28 : sql_idx + 32])[0]
        db_size = page_size * page_count
        if db_size > 0 and sql_idx + db_size <= len(data):
            return data[sql_idx : sql_idx + db_size]
        return data[sql_idx:]

    return None

def extract_character_metadata(sqlite_bytes: bytes) -> Dict[str, Any]:
    """Extracts character metadata from the in-memory SQLite database."""
    meta: Dict[str, Any] = {
        'name': 'Unknown Wizard',
        'house': 'Unknown',
        'xp': 0,
        'perk_points': 0,
        'wand': {},
        'inventory_capacity': 20,
        'gender': 'Unknown',
        'pronoun': 'Unknown'
    }

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp.write(sqlite_bytes)
        tmp_path = tmp.name

    try:
        conn = sqlite3.connect(tmp_path)
        cur = conn.cursor()
        tables = {row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()}

        if 'MiscDataDynamic' in tables:
            rows = cur.execute("SELECT DataOwner, DataName, DataValue FROM MiscDataDynamic;").fetchall()
            misc_dict = {(r[0], r[1]): r[2] for r in rows}

            first_name = misc_dict.get(('Player', 'PlayerFirstName'), '')
            last_name = misc_dict.get(('Player', 'PlayerLastName'), '')
            if first_name or last_name:
                meta['name'] = f"{first_name} {last_name}".strip()

            meta['house'] = misc_dict.get(('Player', 'HouseID'), 'Unknown')
            meta['perk_points'] = int(misc_dict.get(('Player0', 'PerkPoints'), '0'))
            meta['inventory_capacity'] = int(misc_dict.get(('Player0', 'BaseInventoryCapacity'), '20'))
            meta['gender'] = misc_dict.get(('Player', 'GenderVoice'), 'Unknown')
            meta['pronoun'] = misc_dict.get(('Player', 'GenderPronoun'), 'Unknown')

            xp_str = misc_dict.get(('ExperienceManager', 'ExperiencePoints'), '0')
            try:
                meta['xp'] = int(xp_str)
            except ValueError:
                meta['xp'] = 0

            meta['wand'] = {
                'wood': misc_dict.get(('Player', 'WandWood'), '').replace('Wood_', ''),
                'core': misc_dict.get(('Player', 'WandCore'), '').replace('Core', ''),
                'length': misc_dict.get(('Player', 'WandLength'), ''),
                'flexibility': misc_dict.get(('Player', 'WandFlex'), '').replace('Flexibility_', ''),
            }

        conn.close()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return meta
