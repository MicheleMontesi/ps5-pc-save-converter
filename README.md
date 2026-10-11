# Cross-Save Converter (Console ⇄ PC) 🎮 ⇄ 💻

Applicazione Web multipiattaforma con interfaccia grafica per la conversione bidirezionale dei salvataggi tra Console e PC (attualmente specializzata per **Hogwarts Legacy**, espandibile ad altri giochi in futuro).

---

## 🚀 Caratteristiche Principali

* **Conversione Bidirezionale:**
  * **PS5 ➔ PC:** Decomprime i container UE4 GVAS con algoritmi Oodle Kraken esportati da *Garlic Save Manager*, estrae il database SQLite e ricostruisce i file `.sav` PC nativi (`HL-00-00.sav` ... `HL-00-14.sav`).
  * **PC ➔ PS5:** Prende i file `.sav` PC (anche modificati con save editor) e li impacchetta nella gerarchia di cartelle richiesta da *Garlic Save Manager* (`PPSA01603/sdimg_HLxxxx/ue4savegame.ps5.sav`), pronti per essere importati, re-criptati e resignati su PlayStation 5.
* **Architettura Multi-Gioco:**
  * Selettore di gioco pronto per supportare titoli aggiuntivi con logiche dedicate.
  * Al momento è attivo e validato esclusivamente **Hogwarts Legacy**.
* **Anteprima Dati Personaggio in Tempo Reale:**
  * Nome e cognome del personaggio (es. *MichiPino Colapalla*)
  * Casa di Hogwarts (Corvonero, Grifondoro, Serpeverde, Tassorosso) con stemma e colori
  * Dettagli completi della bacchetta (legno, nucleo, lunghezza, flessibilità)
  * Punti talento, livello di esperienza (XP) e capacità dell'inventario
* **Rilevamento Automatico della Cartella di Gioco:**
  * **Windows:** Trova in automatico la cartella `%LOCALAPPDATA%\Hogwarts Legacy\Saved\SaveGames\<UserID>\`.
  * **macOS:** Scansiona le bottiglie Whisky, CrossOver, Wine e Heroic.
  * **Linux / Steam Deck:** Rileva i prefissi Proton di Steam.
* **Installazione & Backup Automatizzati:**
  * Pulsante per installare direttamente i salvataggi nella cartella del gioco.
  * Backup automatico timestampato dei vecchi salvataggi (`Backup_YYYYMMDD_HHMMSS/`) prima della sovrascrittura.
  * Pulizia/rigenerazione automatica dell'indice `SaveGameList.sav` per mostrare subito tutti i salvataggi nel menu di gioco.
* **Download ZIP Pronto all'Uso:**
  * Download immediato dell'archivio (`HogwartsLegacy_PC_Saves.zip` oppure `PPSA01603_Garlic_Ready.zip`).

---

## ⚡ Come Avviare l'Applicazione

### Su macOS e Linux:
1. Apri il terminale nella cartella del progetto.
2. Esegui il launcher:
   ```bash
   ./start.sh
   ```
   *(Il launcher configurerà automaticamente l'ambiente Python e aprirà la Web UI nel browser su `http://127.0.0.1:5050`)*

### Su Windows:
1. Fai doppio clic sul file:
   ```text
   start.bat
   ```
   *(Assicurati di avere Python installato con la spunta "Add Python to PATH")*

---

## 📖 Come Usare

### Da PS5 a PC:
1. Dalla tua PS5 con Jailbreak, usa **Garlic Save Manager** (browser su `http://<IP_PS5>:8082`).
2. Seleziona *Hogwarts Legacy* (`PPSA01603`) e scarica il salvataggio decriptato (es. `PPSA01603_saves_dec.zip`).
3. Nella Web UI seleziona **"Da PS5 a PC"** e trascina il file ZIP (oppure seleziona la cartella locale).
4. Verifica l'anteprima del personaggio.
5. Clicca su **"Installa Direttamente nella Cartella di Gioco"** (il backup verrà creato in automatico) oppure scarica lo ZIP.

### Da PC a PS5:
1. Nella Web UI seleziona **"Da PC a PS5"**.
2. Trascina i tuoi file `.sav` PC (es. `HL-00-00.sav` o uno ZIP con i salvataggi).
3. Scarica lo ZIP convertito (`PPSA01603_Garlic_Ready.zip`).
4. Apri **Garlic Save Manager** sulla PS5 e carica l'archivio per re-importare e ri-criptare il salvataggio sulla console.

---

## 📂 Struttura del Progetto

```text
cross-save-converter/
├── app.py                     # Server Web Flask e API REST
├── converter.py               # Algoritmo Oodle Kraken & GVAS (bidirezionale)
├── game_detector.py           # Scanner percorsi di gioco (Win/Mac/Linux) & backup
├── requirements.txt           # Dipendenze (Flask, pyooz)
├── start.sh                   # Script di avvio per macOS/Linux
├── start.bat                  # Script di avvio per Windows
├── templates/
│   └── index.html             # Pagina Web UI principale
└── static/
    ├── css/style.css          # Foglio di stile dark magico con glassmorphism
    └── js/app.js              # Logica frontend (drag & drop, modal, direzioni)
```
