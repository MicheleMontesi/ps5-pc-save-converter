"""
Flask Web Application for Modular PS5 <-> PC Cross-Save Converter.
Cross-platform Web UI with dynamic game plugin support, real-time preview,
and automated safe installation with backup.
"""

import os
import sys
import uuid
import zipfile
import io
import webbrowser
import threading
import socket
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

from core.registry import GameRegistry
import games  # Auto-registers all game plugins

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# In-memory storage for active sessions
SESSION_CACHE = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/games', methods=['GET'])
def api_games():
    """Returns list of all registered game converters."""
    return jsonify({
        'success': True,
        'games': GameRegistry.list_games()
    })

@app.route('/api/detect-paths', methods=['GET'])
def api_detect_paths():
    """Detects game save directories on system for the selected game."""
    try:
        game_id = request.args.get('game', 'hogwarts-legacy')
        converter = GameRegistry.get(game_id)
        if not converter:
            return jsonify({'success': False, 'error': f"Gioco '{game_id}' non registrato."}), 404

        candidates = converter.find_candidate_save_directories()
        return jsonify({
            'success': True,
            'game': game_id,
            'platform': sys.platform,
            'paths': candidates
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def api_convert():
    try:
        requested_game = request.form.get('game', 'hogwarts-legacy')
        direction = request.form.get('direction', 'ps5_to_pc')

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

        # Auto-detect game if requested or fallback
        detected_game = GameRegistry.detect_game_from_source(stream)
        game_id = detected_game if detected_game else requested_game

        converter = GameRegistry.get(game_id)
        if not converter:
            return jsonify({'success': False, 'error': f"Il gioco '{game_id}' non è attualmente supportato."}), 400

        if not converter.is_active:
            return jsonify({'success': False, 'error': f"Il supporto per '{converter.display_name}' è in fase di sviluppo."}), 400

        # Execute conversion via modular converter
        if direction == 'pc_to_ps5':
            result = converter.convert_pc_to_ps5(stream)
        else:
            result = converter.convert_ps5_to_pc(stream)

        if not result['saves']:
            error_msg = "; ".join(result['errors']) if result['errors'] else "Nessun salvataggio valido riconosciuto nel file."
            return jsonify({'success': False, 'error': error_msg}), 400

        session_id = str(uuid.uuid4())
        SESSION_CACHE[session_id] = {
            'game_id': game_id,
            'character': result['character'],
            'saves': result['saves'],
            'direction': direction,
            'original_filename': orig_name
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'game_id': game_id,
            'game_name': converter.display_name,
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
        requested_game = data.get('game', 'hogwarts-legacy')
        direction = data.get('direction', 'ps5_to_pc')
        local_path = data.get('path', '').strip()

        if not local_path or not os.path.exists(local_path):
            return jsonify({'success': False, 'error': f"Percorso non trovato: {local_path}"}), 400

        detected_game = GameRegistry.detect_game_from_source(local_path)
        game_id = detected_game if detected_game else requested_game

        converter = GameRegistry.get(game_id)
        if not converter:
            return jsonify({'success': False, 'error': f"Il gioco '{game_id}' non è attualmente supportato."}), 400

        if direction == 'pc_to_ps5':
            result = converter.convert_pc_to_ps5(local_path)
        else:
            result = converter.convert_ps5_to_pc(local_path)

        if not result['saves']:
            return jsonify({'success': False, 'error': "Nessun salvataggio valido trovato nel percorso."}), 400

        session_id = str(uuid.uuid4())
        SESSION_CACHE[session_id] = {
            'game_id': game_id,
            'character': result['character'],
            'saves': result['saves'],
            'direction': direction,
            'original_filename': os.path.basename(local_path)
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'game_id': game_id,
            'game_name': converter.display_name,
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
    game_id = session_data.get('game_id', 'hogwarts-legacy')

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname, data in saves.items():
            zf.writestr(fname, data)

    zip_buffer.seek(0)
    if direction == 'pc_to_ps5':
        dl_name = f"{game_id.upper()}_PS5_Garlic_Ready.zip"
    else:
        dl_name = f"{game_id.replace('-', '_').title()}_PC_Saves.zip"

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

        session_data = SESSION_CACHE[session_id]
        saves = session_data['saves']
        game_id = session_data.get('game_id', 'hogwarts-legacy')

        converter = GameRegistry.get(game_id)
        if not converter:
            return jsonify({'success': False, 'error': f"Convertitore per '{game_id}' non trovato."}), 400

        install_res = converter.install_saves(target_dir, saves, do_backup=do_backup)

        return jsonify({
            'success': True,
            'installed_files': install_res['installed_files'],
            'backup_folder': install_res['backup']['folder'] if install_res['backup'] else None,
            'target_dir': install_res['target_dir']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    threading.Timer(1.2, lambda: open_browser(port)).start()
    print("=" * 60)
    print(f"[*] PS5 ⇄ PC Save Converter Web UI attiva:")
    print(f"    • Locale (Mac/PC):   http://127.0.0.1:{port}")
    if local_ip != '127.0.0.1':
        print(f"    • Da Windows / LAN:  http://{local_ip}:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
