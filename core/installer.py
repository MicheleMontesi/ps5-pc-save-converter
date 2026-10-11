"""
Safe backup and save installation utility.
Creates timestamped backups before overwriting any game save files.
"""

import os
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def backup_and_install_saves(
    target_dir: str,
    new_saves: Dict[str, bytes],
    do_backup: bool = True,
    index_files_to_refresh: Optional[list] = None
) -> Dict[str, Any]:
    """
    Backs up existing saves in target_dir and writes new_saves into it.

    Args:
        target_dir: Destination directory path on local disk
        new_saves: Mapping { filename: binary_content }
        do_backup: Whether to create a Backup_YYYYMMDD_HHMMSS folder
        index_files_to_refresh: List of index files (e.g. ['SaveGameList.sav'])
    """
    path = Path(target_dir)
    if not path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

    backup_info = None
    if do_backup:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = path / f"Backup_{timestamp}"
        backup_folder.mkdir(parents=True, exist_ok=True)

        backed_up_files = []
        for file in path.glob("*.sav"):
            shutil.copy2(file, backup_folder / file.name)
            backed_up_files.append(file.name)

        backup_info = {
            'folder': str(backup_folder),
            'files': backed_up_files
        }

    # If specific index files need unlinking when not explicitly provided in new_saves
    if index_files_to_refresh:
        for idx_file in index_files_to_refresh:
            if idx_file not in new_saves:
                p = path / idx_file
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

    # Write new saves
    installed_files = []
    for filename, content in new_saves.items():
        dst_path = path / filename
        with open(dst_path, 'wb') as f:
            f.write(content)
        installed_files.append(filename)

    return {
        'success': True,
        'installed_files': installed_files,
        'backup': backup_info,
        'target_dir': str(path)
    }


def backup_existing_saves(target_dir: str) -> Optional[str]:
    """Creates a timestamped backup of all .sav files in target_dir."""
    res = backup_and_install_saves(target_dir, {}, do_backup=True)
    if res['backup']:
        return res['backup']['folder']
    return None
