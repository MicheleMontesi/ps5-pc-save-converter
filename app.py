"""
Flask Web Application for Hogwarts Legacy Save Converter.
Cross-platform Web UI for converting PS5 saves to PC, previewing character data,
and automated installation with backup support.
"""

import os
import sys
import uuid
import zipfile
import io
import webbrowser
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

from converter import process_archive_or_files
from game_detector import find_candidate_save_directories, backup_and_install_saves

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# In-memory storage for active sessions
SESSION_CACHE = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/detect-paths', methods=['GET'])
def api_detect_paths():
    try:
        candidates = find_candidate_save_directories()
        return jsonify({
            'success': True,
            'platform': sys.platform,
            'paths': candidates
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def api_convert():
    try:
        game = request.form.get('game', 'hogwarts-legacy')
        direction = request.form.get('direction', 'ps5_to_pc')

        if game != 'hogwarts-legacy':
            return jsonify({'success': False, 'error': f"Il gioco '{game}' non è supportato. Al momento è supportato esclusivamente Hogwarts Legacy."}), 400

        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': 'Nessun file caricato.'}), 400

        if len(files) == 1:
            uploaded_file = files[0]
            file_bytes = uploaded_file.read()
            stream = io.BytesIO(file_bytes)
            orig_name = uploaded_file.filename
        else:
            # Bundle multiple files into in-memory zip
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    zf.writestr(f.filename, f.read())
            zip_buffer.seek(0)
            stream = zip_buffer
            orig_name = f"{len(files)}_files.zip"

        result = process_archive_or_files(stream, direction=direction)
        if not result['saves']:
            error_msg = "; ".join(result['errors']) if result['errors'] else "Nessun salvataggio valido riconosciuto nel file."
            return jsonify({'success': False, 'error': error_msg}), 400

        session_id = str(uuid.uuid4())
        SESSION_CACHE[session_id] = {
            'character': result['character'],
            'saves': result['saves'],
            'direction': direction,
            'original_filename': orig_name
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'direction': direction,
            'character': result['character'],
            'converted_slots': list(result['saves'].keys()),
            'count': len(result['saves']),
            'errors': result['errors']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/convert-local-path', methods=['POST'])
def api_convert_local_path():
    """Allows converting directly from a local path on the machine"""
    try:
        data = request.get_json() or {}
        game = data.get('game', 'hogwarts-legacy')
        direction = data.get('direction', 'ps5_to_pc')

        if game != 'hogwarts-legacy':
            return jsonify({'success': False, 'error': f"Il gioco '{game}' non è supportato. Al momento è supportato esclusivamente Hogwarts Legacy."}), 400

        local_path = data.get('path', '').strip()
        if not local_path or not os.path.exists(local_path):
            return jsonify({'success': False, 'error': f"Percorso non trovato: {local_path}"}), 400

        result = process_archive_or_files(local_path, direction=direction)

        if not result['saves']:
            return jsonify({'success': False, 'error': "Nessun salvataggio valido trovato nel percorso."}), 400

        session_id = str(uuid.uuid4())
        SESSION_CACHE[session_id] = {
            'character': result['character'],
            'saves': result['saves'],
            'direction': direction,
            'original_filename': os.path.basename(local_path)
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'direction': direction,
            'character': result['character'],
            'converted_slots': list(result['saves'].keys()),
            'count': len(result['saves']),
            'errors': result['errors']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/<session_id>', methods=['GET'])
def api_download(session_id):
    if session_id not in SESSION_CACHE:
        return "Sessione scaduta o non valida.", 404

    session_data = SESSION_CACHE[session_id]
    saves = session_data['saves']
    direction = session_data.get('direction', 'ps5_to_pc')

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname, data in saves.items():
            zf.writestr(fname, data)

    zip_buffer.seek(0)
    dl_name = 'PPSA01603_Garlic_Ready.zip' if direction == 'pc_to_ps5' else 'HogwartsLegacy_PC_Saves.zip'
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=dl_name
    )

@app.route('/api/install', methods=['POST'])
def api_install():
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        target_dir = data.get('target_dir', '').strip()
        do_backup = data.get('backup', True)

        if not session_id or session_id not in SESSION_CACHE:
            return jsonify({'success': False, 'error': 'Sessione non valida.'}), 400

        if not target_dir:
            return jsonify({'success': False, 'error': 'Percorso di destinazione mancante.'}), 400

        saves = SESSION_CACHE[session_id]['saves']
        install_res = backup_and_install_saves(target_dir, saves, do_backup=do_backup)

        return jsonify({
            'success': True,
            'installed_files': install_res['installed_files'],
            'backup_folder': install_res['backup']['folder'] if install_res['backup'] else None,
            'target_dir': install_res['target_dir']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def open_browser(port):
    webbrowser.open(f"http://127.0.0.1:{port}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    local_ip = get_local_ip()
    # Open browser automatically on host machine after 1.2s
    threading.Timer(1.2, lambda: open_browser(port)).start()
    print("=" * 60)
    print(f"[*] PS5 ⇄ PC Save Converter Web UI attiva:")
    print(f"    • Locale (Mac):      http://127.0.0.1:{port}")
    if local_ip != '127.0.0.1':
        print(f"    • Da Windows / LAN:  http://{local_ip}:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
