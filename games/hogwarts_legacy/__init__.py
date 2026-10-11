"""
Hogwarts Legacy Game Converter Module.
Implements BaseGameConverter interface.
"""

import os
import zipfile
from typing import Dict, Any, List

from core.base import BaseGameConverter
from .converter import (
    patch_ps5_to_pc_sav,
    patch_pc_to_ps5_sav,
    extract_sqlite_from_sav,
    extract_character_metadata,
    PS5_TO_PC_MAP,
    PC_TO_PS5_MAP
)
from .detector import find_hogwarts_save_directories


class HogwartsLegacyConverter(BaseGameConverter):
    """Converter for Hogwarts Legacy saves between PS5 and PC."""

    @property
    def game_id(self) -> str:
        return 'hogwarts-legacy'

    @property
    def display_name(self) -> str:
        return 'Hogwarts Legacy'

    @property
    def title_ids(self) -> List[str]:
        # Includes European and North American title IDs
        return ['PPSA01603', 'PPSA01602', 'CUSA12824']

    @property
    def format_description(self) -> str:
        return 'UE4 GVAS + Oodle Kraken + SQLite'

    @property
    def is_active(self) -> bool:
        return True

    def convert_ps5_to_pc(self, input_source: Any) -> Dict[str, Any]:
        result = {'character': None, 'saves': {}, 'errors': []}

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

            pc_sav = patch_ps5_to_pc_sav(raw_data)
            result['saves'][target_name] = pc_sav

            if not result['character']:
                try:
                    sql_db = extract_sqlite_from_sav(raw_data)
                    if sql_db:
                        result['character'] = extract_character_metadata(sql_db)
                except Exception:
                    pass

        # 1. Directory
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

        # 2. ZIP
        zf = None
        if isinstance(input_source, (str, os.PathLike)) and str(input_source).endswith('.zip'):
            zf = zipfile.ZipFile(input_source)
        elif hasattr(input_source, 'read'):
            try:
                zf = zipfile.ZipFile(input_source)
            except Exception:
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

        # 3. Single file
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

    def convert_pc_to_ps5(self, input_source: Any, title_id: str = "PPSA01603") -> Dict[str, Any]:
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

        # 1. Directory
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

        # 2. ZIP
        zf = None
        if isinstance(input_source, (str, os.PathLike)) and str(input_source).endswith('.zip'):
            zf = zipfile.ZipFile(input_source)
        elif hasattr(input_source, 'read'):
            try:
                zf = zipfile.ZipFile(input_source)
            except Exception:
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

        # 3. Single file
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

    def find_candidate_save_directories(self) -> List[Dict[str, Any]]:
        return find_hogwarts_save_directories()
