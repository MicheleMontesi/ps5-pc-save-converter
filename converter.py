"""
Core conversion logic for Cross-Save Converter (Console <-> PC).
Supports:
1. PS5 -> PC:
   - Preserves Oodle Kraken chunk compression required by PC Hogwarts Legacy and modern Save Editors.
   - Patches GVAS header platform identifiers (PS5 -> Windows).
   - Maps Garlic Save Manager layout (sdimg_HLxxxx, sdimg_SaveGameList, sdimg_SavedUserOptions)
     to PC filenames (HL-00-00.sav, SaveGameList.sav, SavedUserOptions.sav).
   - Decompresses in-memory database to provide character metadata preview.
2. PC -> PS5:
   - Patches GVAS header platform identifiers (Windows -> PS5).
   - Packages PC saves into Garlic Save Manager layout ready for re-encryption and resigning.
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
FULL_DB_NEEDLE = b'\x11\x00\x00\x00RawDatabaseImage\x00'

# Mapping between PS5 Garlic directory names and PC save names
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

DEFAULT_TITLE_ID = "PPSA01603"

# Byte patterns for Platform and ExclusivePlatform FStrings in GVAS
PS5_PLATFORM_BYTES = b'\t\x00\x00\x00Platform\x00\x0c\x00\x00\x00StrProperty\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00PS5\x00'
WIN_PLATFORM_BYTES = b'\t\x00\x00\x00Platform\x00\x0c\x00\x00\x00StrProperty\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00Windows\x00'

PS5_EXCL_PLATFORM_BYTES = b'\x12\x00\x00\x00ExclusivePlatform\x00\x0c\x00\x00\x00StrProperty\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00PS5\x00'
WIN_EXCL_PLATFORM_BYTES = b'\x12\x00\x00\x00ExclusivePlatform\x00\x0c\x00\x00\x00StrProperty\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00Windows\x00'

def patch_ps5_to_pc_sav(data: bytes) -> bytes:
    """
    Patches a PS5 GVAS save file for PC:
    Replaces Platform and ExclusivePlatform FStrings from 'PS5' to 'Windows'.
    Preserves all Oodle Kraken compressed data, RawExclusiveImage, and RawMiniMapImage bit-for-bit.
    """
    out = data
    if PS5_PLATFORM_BYTES in out:
        out = out.replace(PS5_PLATFORM_BYTES, WIN_PLATFORM_BYTES, 1)
    if PS5_EXCL_PLATFORM_BYTES in out:
        out = out.replace(PS5_EXCL_PLATFORM_BYTES, WIN_EXCL_PLATFORM_BYTES, 1)
    return out

def patch_pc_to_ps5_sav(data: bytes) -> bytes:
    """
    Patches a PC GVAS save file for PS5:
    Replaces Platform and ExclusivePlatform FStrings from 'Windows' to 'PS5'.
    Preserves all Oodle Kraken compressed data, RawExclusiveImage, and RawMiniMapImage bit-for-bit.
    """
    out = data
    if WIN_PLATFORM_BYTES in out:
        out = out.replace(WIN_PLATFORM_BYTES, PS5_PLATFORM_BYTES, 1)
    if WIN_EXCL_PLATFORM_BYTES in out:
        out = out.replace(WIN_EXCL_PLATFORM_BYTES, PS5_EXCL_PLATFORM_BYTES, 1)
    return out

def extract_sqlite_from_sav(data: bytes) -> Optional[bytes]:
    """
    Extracts raw SQLite database from either an Oodle-compressed or uncompressed save.
    Used for reading character metadata.
    """
    if RAW_DB_NEEDLE not in data:
        return None

    needle_idx = data.index(RAW_DB_NEEDLE)
    
    # 1. Check if compressed with Oodle Kraken
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

    # 2. Check if already uncompressed SQLite
    if SQLITE_MAGIC in data[needle_idx:]:
        sql_idx = data.index(SQLITE_MAGIC, needle_idx)
        # SQLite database size can be calculated from database header (page_size * page_count)
        page_size = struct.unpack('>H', data[sql_idx + 16 : sql_idx + 18])[0]
        page_count = struct.unpack('>I', data[sql_idx + 28 : sql_idx + 32])[0]
        db_size = page_size * page_count
        if db_size > 0 and sql_idx + db_size <= len(data):
            return data[sql_idx : sql_idx + db_size]
        return data[sql_idx:]

    return None

def extract_character_metadata(sqlite_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts high-level character info from the SQLite database bytes.
    """
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

            # Experience
            xp_str = misc_dict.get(('ExperienceManager', 'ExperiencePoints'), '0')
            try:
                meta['xp'] = int(xp_str)
            except ValueError:
                meta['xp'] = 0

            # Wand
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

def convert_ps5_to_pc(input_source) -> Dict[str, Any]:
    """
    Direction: PS5 -> PC
    Takes decrypted PS5 folder or ZIP from Garlic Save Manager.
    Produces native, Oodle-compressed PC .sav files compatible with PC Hogwarts Legacy and Save Editors.
    """
    result = {'character': None, 'saves': {}, 'errors': []}

    # Helper to process single file bytes
    def process_file_bytes(fname: str, raw_data: bytes, parent_folder: str = ''):
        target_name = PS5_TO_PC_MAP.get(parent_folder)
        if not target_name:
            if fname.startswith('HL-') or fname.startswith('HL00'):
                target_name = fname if fname.startswith('HL-') else f"{fname[:2]}-{fname[2:4]}-{fname[4:]}"
            elif fname in ('SaveGameList.sav', 'SavedUserOptions.sav'):
                target_name = fname
            elif 'SaveGameList' in parent_folder or 'SaveGameList' in fname:
                target_name = 'SaveGameList.sav'
            elif 'SavedUserOptions' in parent_folder or 'SavedUserOptions' in fname:
                target_name = 'SavedUserOptions.sav'
            else:
                return

        # Patch Platform tags for PC (PS5 -> Windows)
        pc_sav = patch_ps5_to_pc_sav(raw_data)
        result['saves'][target_name] = pc_sav

        # In-memory decompression to extract character preview metadata
        if not result['character']:
            try:
                sql_db = extract_sqlite_from_sav(raw_data)
                if sql_db:
                    result['character'] = extract_character_metadata(sql_db)
            except Exception as e:
                pass

    # 1. If directory
    if isinstance(input_source, (str, os.PathLike)) and os.path.isdir(input_source):
        for root, _, files in os.walk(input_source):
            for file in files:
                if file.endswith('ue4savegame.ps5.sav') or (file.endswith('.sav') and not file.startswith('.')):
                    parent_dir = os.path.basename(root)
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'rb') as f:
                            raw_data = f.read()
                        process_file_bytes(file, raw_data, parent_dir)
                    except Exception as e:
                        result['errors'].append(f"Errore su {file}: {str(e)}")
        return result

    # 2. If ZIP
    zf = None
    if isinstance(input_source, (str, os.PathLike)) and str(input_source).endswith('.zip'):
        zf = zipfile.ZipFile(input_source)
    elif hasattr(input_source, 'read'):
        try:
            zf = zipfile.ZipFile(input_source)
        except (zipfile.BadZipFile, io.UnsupportedOperation):
            zf = None

    if zf:
        with zf:
            for item in zf.infolist():
                if item.filename.endswith('ue4savegame.ps5.sav') or (item.filename.endswith('.sav') and not os.path.basename(item.filename).startswith('.')):
                    filename = os.path.basename(item.filename)
                    parent_dir = os.path.basename(os.path.dirname(item.filename))
                    try:
                        raw_data = zf.read(item)
                        process_file_bytes(filename, raw_data, parent_dir)
                    except Exception as e:
                        result['errors'].append(f"Errore su {item.filename}: {str(e)}")
        return result

    # 3. If single file
    if hasattr(input_source, 'seek'):
        input_source.seek(0)
        data = input_source.read()
    else:
        with open(input_source, 'rb') as f:
            data = f.read()

    try:
        pc_sav = patch_ps5_to_pc_sav(data)
        result['saves']['HL-00-00.sav'] = pc_sav
        sql_db = extract_sqlite_from_sav(data)
        if sql_db:
            result['character'] = extract_character_metadata(sql_db)
    except Exception as e:
        result['errors'].append(f"Conversione fallita: {str(e)}")

    return result

def convert_pc_to_ps5(input_source, title_id: str = DEFAULT_TITLE_ID) -> Dict[str, Any]:
    """
    Direction: PC -> PS5
    Takes PC .sav files and packages them into the Garlic Save Manager layout:
    <title_id>/sdimg_HLxxxx/ue4savegame.ps5.sav, sdimg_SaveGameList, etc.
    """
    result = {'character': None, 'saves': {}, 'errors': []}

    def process_pc_file(fname: str, raw_data: bytes):
        ps5_dir = PC_TO_PS5_MAP.get(fname)
        if not ps5_dir:
            if fname.startswith('HL-') or fname.startswith('HL00'):
                clean_name = fname.replace('-', '')
                ps5_dir = f"sdimg_{clean_name[:-4]}"
            elif fname == 'SaveGameList.sav':
                ps5_dir = 'sdimg_SaveGameList'
            elif fname == 'SavedUserOptions.sav':
                ps5_dir = 'sdimg_SavedUserOptions'
            else:
                return

        # Patch Platform tags for PS5 (Windows -> PS5)
        ps5_sav = patch_pc_to_ps5_sav(raw_data)
        target_key = f"{title_id}/{ps5_dir}/ue4savegame.ps5.sav"
        result['saves'][target_key] = ps5_sav

        if not result['character']:
            try:
                sql_db = extract_sqlite_from_sav(raw_data)
                if sql_db:
                    result['character'] = extract_character_metadata(sql_db)
            except Exception:
                pass

    # 1. If directory
    if isinstance(input_source, (str, os.PathLike)) and os.path.isdir(input_source):
        for root, _, files in os.walk(input_source):
            for file in files:
                if file.endswith('.sav') and not file.startswith('.'):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'rb') as f:
                            sav_bytes = f.read()
                        process_pc_file(file, sav_bytes)
                    except Exception as e:
                        result['errors'].append(f"Errore su {file}: {str(e)}")
        return result

    # 2. If ZIP
    zf = None
    if isinstance(input_source, (str, os.PathLike)) and str(input_source).endswith('.zip'):
        zf = zipfile.ZipFile(input_source)
    elif hasattr(input_source, 'read'):
        try:
            zf = zipfile.ZipFile(input_source)
        except (zipfile.BadZipFile, io.UnsupportedOperation):
            zf = None

    if zf:
        with zf:
            for item in zf.infolist():
                fname = os.path.basename(item.filename)
                if fname.endswith('.sav') and not fname.startswith('.'):
                    try:
                        sav_bytes = zf.read(item)
                        process_pc_file(fname, sav_bytes)
                    except Exception as e:
                        result['errors'].append(f"Errore su {item.filename}: {str(e)}")
        return result

    # 3. Single PC save file
    if hasattr(input_source, 'seek'):
        input_source.seek(0)
        data = input_source.read()
    else:
        with open(input_source, 'rb') as f:
            data = f.read()

    try:
        ps5_sav = patch_pc_to_ps5_sav(data)
        target_key = f"{title_id}/sdimg_HL0000/ue4savegame.ps5.sav"
        result['saves'][target_key] = ps5_sav
        sql_db = extract_sqlite_from_sav(data)
        if sql_db:
            result['character'] = extract_character_metadata(sql_db)
    except Exception as e:
        result['errors'].append(f"Conversione fallita: {str(e)}")

    return result

def process_archive_or_files(input_source, direction: str = 'ps5_to_pc') -> Dict[str, Any]:
    """Unified entrypoint supporting direction selection"""
    if direction == 'pc_to_ps5':
        return convert_pc_to_ps5(input_source)
    return convert_ps5_to_pc(input_source)
