#!/usr/bin/env bash
# Cross-Save Converter - Launcher for macOS & Linux

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  PS5 ⇄ PC Save Converter - Web UI"
echo "=========================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[-] Errore: Python 3 non è installato."
    echo "    Installalo da https://www.python.org/ o tramite Homebrew: brew install python"
    exit 1
fi

# Detect if existing venv was created in a different folder (renamed/moved)
if [ -d "venv" ]; then
    if [ ! -f "venv/bin/activate" ] || ! grep -q "$DIR" "venv/bin/activate" 2>/dev/null; then
        echo "[*] Rilevato cambio di percorso cartella, ricreazione ambiente virtuale..."
        rm -rf venv
    fi
fi

# Create virtual environment if it does not exist
if [ ! -d "venv" ]; then
    echo "[*] Creazione ambiente virtuale Python (venv)..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install / update requirements using venv pip
echo "[*] Verifica dipendenze (Flask, pyooz)..."
"$DIR/venv/bin/pip" install -q -r requirements.txt

echo "[*] Avvio Web UI..."
"$DIR/venv/bin/python3" app.py
