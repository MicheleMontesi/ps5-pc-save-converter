document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const uploadSection = document.getElementById('uploadSection');
    const resultSection = document.getElementById('resultSection');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressLabel = document.getElementById('progressLabel');

    const toggleLocalPath = document.getElementById('toggleLocalPath');
    const localPathDrawer = document.getElementById('localPathDrawer');
    const localPathInput = document.getElementById('localPathInput');
    const btnConvertLocal = document.getElementById('btnConvertLocal');

    const characterCard = document.getElementById('characterCard');
    const slotCount = document.getElementById('slotCount');
    const slotTagsList = document.getElementById('slotTagsList');

    const detectedFoldersBox = document.getElementById('detectedFoldersBox');
    const detectedList = document.getElementById('detectedList');
    const targetDirInput = document.getElementById('targetDirInput');
    const backupCheckbox = document.getElementById('backupCheckbox');
    const btnInstall = document.getElementById('btnInstall');
    const btnDownloadZip = document.getElementById('btnDownloadZip');
    const btnReset = document.getElementById('btnReset');

    const modalBackdrop = document.getElementById('modalBackdrop');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    const modalClose = document.getElementById('modalClose');
    const modalConfirm = document.getElementById('modalConfirm');

    // Direction switcher elements
    const dirPs5ToPc = document.getElementById('dirPs5ToPc');
    const dirPcToPs5 = document.getElementById('dirPcToPs5');
    const step1Title = document.getElementById('step1Title');
    const step1Subtitle = document.getElementById('step1Subtitle');
    const dropzoneText = document.getElementById('dropzoneText');
    const gameSelect = document.getElementById('gameSelect');
    const gameMethodText = document.getElementById('gameMethodText');
    const gameMethodDot = document.getElementById('gameMethodDot');

    let currentSessionId = null;
    let currentDirection = 'ps5_to_pc';
    let detectedPaths = [];
    let registeredGames = [];

    const HOUSE_DATA = {
        'Ravenclaw': { name: 'Corvonero', class: 'house-Ravenclaw', icon: '🦅' },
        'Gryffindor': { name: 'Grifondoro', class: 'house-Gryffindor', icon: '🦁' },
        'Slytherin': { name: 'Serpeverde', class: 'house-Slytherin', icon: '🐍' },
        'Hufflepuff': { name: 'Tassorosso', class: 'house-Hufflepuff', icon: '🦡' },
        'Unknown': { name: 'Non Assegnata', class: 'house-Unknown', icon: '🏰' }
    };

    async function loadGames() {
        try {
            const res = await fetch('/api/games');
            const data = await res.json();
            if (data.success && data.games) {
                registeredGames = data.games;
                renderGameSelect(registeredGames);
            }
        } catch (e) {
            console.warn('Errore nel caricamento dei moduli gioco:', e);
        }
    }

    function renderGameSelect(games) {
        if (!gameSelect) return;
        const currentVal = gameSelect.value || 'hogwarts-legacy';
        gameSelect.innerHTML = '';

        games.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = g.name + (g.active ? '' : ' (In arrivo)');
            opt.disabled = !g.active;
            if (g.id === currentVal) opt.selected = true;
            gameSelect.appendChild(opt);
        });

        const moreOpt = document.createElement('option');
        moreOpt.value = 'more';
        moreOpt.textContent = '+ Aggiungi altri giochi (Modulo Python)';
        moreOpt.disabled = true;
        gameSelect.appendChild(moreOpt);

        updateGameBadge();
    }

    function updateGameBadge() {
        const selectedId = gameSelect ? gameSelect.value : 'hogwarts-legacy';
        const game = registeredGames.find(g => g.id === selectedId);
        if (game && gameMethodText) {
            gameMethodText.textContent = `Supportato: ${game.format || 'Formato Nativo'}`;
            if (gameMethodDot) {
                gameMethodDot.className = game.active ? 'dot-active' : 'dot-pending';
            }
        }
    }

    if (gameSelect) {
        gameSelect.addEventListener('change', () => {
            updateGameBadge();
            loadDetectedPaths(gameSelect.value);
        });
    }

    function updateDirectionUI() {
        if (currentDirection === 'ps5_to_pc') {
            dirPs5ToPc.classList.add('active');
            dirPcToPs5.classList.remove('active');
            step1Title.textContent = '1. Seleziona il Salvataggio PS5';
            step1Subtitle.innerHTML = 'Carica il file ZIP decriptato da Garlic Save Manager (es. <code>PPSA01603_saves_dec.zip</code>) oppure un singolo file <code>.sav</code>';
            dropzoneText.innerHTML = 'Trascina qui il file <strong>.ZIP</strong> o <strong>.SAV</strong> di PS5';
            btnInstall.style.display = 'inline-flex';
            btnDownloadZip.querySelector('span').textContent = 'Scarica Archivio ZIP (per PC)';
        } else {
            dirPcToPs5.classList.add('active');
            dirPs5ToPc.classList.remove('active');
            step1Title.textContent = '1. Seleziona il Salvataggio PC';
            step1Subtitle.innerHTML = 'Carica i file <code>HL-00-*.sav</code> del tuo PC oppure una cartella/ZIP contenente i tuoi salvataggi PC';
            dropzoneText.innerHTML = 'Trascina qui i file <strong>.SAV</strong> o <strong>.ZIP</strong> di PC';
            btnInstall.style.display = 'none'; // Auto install is only for local PC game folders
            btnDownloadZip.querySelector('span').textContent = 'Scarica Pacchetto per Garlic Save Manager (PS5)';
        }
    }

    dirPs5ToPc.addEventListener('click', () => {
        currentDirection = 'ps5_to_pc';
        updateDirectionUI();
    });

    dirPcToPs5.addEventListener('click', () => {
        currentDirection = 'pc_to_ps5';
        updateDirectionUI();
    });

    // Prevent default drag behaviors on window to prevent browser from navigating away
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        window.addEventListener(eventName, (e) => {
            e.preventDefault();
        }, false);
    });

    // Dropzone highlight & drag handlers
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
        fileInput.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'dragend'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
        fileInput.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    // Drop handlers
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
        const files = e.dataTransfer ? e.dataTransfer.files : null;
        if (files && files.length > 0) {
            uploadAndConvert(files);
        }
    });

    fileInput.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
        const files = e.dataTransfer ? e.dataTransfer.files : null;
        if (files && files.length > 0) {
            uploadAndConvert(files);
        }
    });

    // File input change handler (native file dialog selection)
    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length > 0) {
            uploadAndConvert(fileInput.files);
        }
    });

    // Toggle local path drawer
    toggleLocalPath.addEventListener('click', () => {
        const isHidden = localPathDrawer.style.display === 'none';
        localPathDrawer.style.display = isHidden ? 'block' : 'none';
        toggleLocalPath.querySelector('.arrow-indicator').textContent = isHidden ? '▲' : '▼';
    });

    btnConvertLocal.addEventListener('click', async () => {
        const path = localPathInput.value.trim();
        if (!path) return;

        const selectedGame = gameSelect ? gameSelect.value : 'hogwarts-legacy';
        const gameObj = registeredGames.find(g => g.id === selectedGame);
        if (gameObj && !gameObj.active) {
            showModal('Modulo in sviluppo', `Il supporto per "${gameObj.name}" è attualmente in fase di sviluppo.`);
            return;
        }

        showProgress(`Conversione in corso (${currentDirection === 'ps5_to_pc' ? 'PS5 ➔ PC' : 'PC ➔ PS5'})...`);
        try {
            const res = await fetch('/api/convert-local-path', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path, game: selectedGame, direction: currentDirection })
            });
            const data = await res.json();
            handleConversionResponse(data);
        } catch (e) {
            showModal('Errore di connessione', e.message);
        } finally {
            hideProgress();
        }
    });

    async function uploadAndConvert(files) {
        if (!files) return;
        const fileList = (files instanceof FileList || Array.isArray(files)) ? Array.from(files) : [files];
        if (fileList.length === 0) return;

        const selectedGame = gameSelect ? gameSelect.value : 'hogwarts-legacy';
        const gameObj = registeredGames.find(g => g.id === selectedGame);
        if (gameObj && !gameObj.active) {
            showModal('Modulo in sviluppo', `Il supporto per "${gameObj.name}" è attualmente in fase di sviluppo.`);
            return;
        }

        const labelName = fileList.length === 1 ? `"${fileList[0].name}"` : `${fileList.length} file`;
        showProgress(`Caricamento e conversione (${currentDirection === 'ps5_to_pc' ? 'PS5 ➔ PC' : 'PC ➔ PS5'}) di ${labelName}...`);

        const formData = new FormData();
        fileList.forEach(file => {
            formData.append('file', file);
        });
        formData.append('game', selectedGame);
        formData.append('direction', currentDirection);

        try {
            const res = await fetch('/api/convert', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            handleConversionResponse(data);
        } catch (e) {
            showModal('Errore', 'Impossibile completare la conversione: ' + e.message);
        } finally {
            hideProgress();
            // Reset input value to allow re-uploading the same file
            fileInput.value = '';
        }
    }

    function handleConversionResponse(data) {
        if (!data.success) {
            showModal('Conversione Fallita', data.error || 'Errore sconosciuto durante la conversione.');
            return;
        }

        currentSessionId = data.session_id;

        // Auto-switch game in UI if auto-detected
        if (data.game_id && gameSelect && gameSelect.value !== data.game_id) {
            gameSelect.value = data.game_id;
            updateGameBadge();
            loadDetectedPaths(data.game_id);
        }

        renderCharacterInfo(data.character);
        renderSlots(data.converted_slots);

        uploadSection.style.display = 'none';
        resultSection.style.display = 'block';
    }

    function renderCharacterInfo(char) {
        if (!char) {
            characterCard.innerHTML = `
                <div class="char-badge-card">
                    <div class="char-crest house-Unknown">🎮</div>
                    <div class="char-info">
                        <div class="char-name">Salvataggi Convertiti</div>
                        <p style="color: var(--text-secondary); margin: 4px 0 0 0; font-size: 0.9rem;">
                            Tutti gli slot di salvataggio sono pronti per essere installati o scaricati.
                        </p>
                    </div>
                </div>
            `;
            return;
        }

        const houseInfo = (char.house && HOUSE_DATA[char.house]) ? HOUSE_DATA[char.house] : null;
        const wand = char.wand || {};
        const wandStr = [
            wand.wood ? `Legno di ${wand.wood}` : '',
            wand.core ? `Nucleo di ${wand.core}` : '',
            wand.length ? `Lunghezza ${wand.length}` : '',
            wand.flexibility ? `(${wand.flexibility})` : ''
        ].filter(Boolean).join(' • ');

        let metaHtml = '';
        if (houseInfo) metaHtml += `<span class="meta-pill">Casa: <strong>${houseInfo.name}</strong></span>`;
        if (char.xp !== undefined) metaHtml += `<span class="meta-pill">Esperienza: <strong>${char.xp.toLocaleString()} XP</strong></span>`;
        if (char.level !== undefined) metaHtml += `<span class="meta-pill">Livello: <strong>${char.level}</strong></span>`;
        if (char.perk_points !== undefined) metaHtml += `<span class="meta-pill">Punti Talento: <strong>${char.perk_points}</strong></span>`;
        if (char.inventory_capacity !== undefined) metaHtml += `<span class="meta-pill">Capacità Inventario: <strong>${char.inventory_capacity}</strong></span>`;

        const icon = houseInfo ? houseInfo.icon : '🧙';
        const crestClass = houseInfo ? houseInfo.class : 'house-Unknown';

        characterCard.innerHTML = `
            <div class="char-badge-card">
                <div class="char-crest ${crestClass}">
                    ${icon}
                </div>
                <div class="char-info">
                    <div class="char-name">${escapeHtml(char.name || 'Salvataggio Giocatore')}</div>
                    ${metaHtml ? `<div class="char-meta-row">${metaHtml}</div>` : ''}
                    ${wandStr ? `<div class="wand-box"><strong>Bacchetta:</strong> ${escapeHtml(wandStr)}</div>` : ''}
                </div>
            </div>
        `;
    }

    function renderSlots(slots) {
        slotCount.textContent = slots.length;
        slotTagsList.innerHTML = '';
        slots.forEach(slot => {
            const span = document.createElement('span');
            span.className = 'slot-badge';
            span.textContent = slot;
            slotTagsList.appendChild(span);
        });
    }

    // Download ZIP
    btnDownloadZip.addEventListener('click', () => {
        if (!currentSessionId) return;
        window.location.href = `/api/download/${currentSessionId}`;
    });

    // Install Directly
    btnInstall.addEventListener('click', async () => {
        const targetDir = targetDirInput.value.trim();
        if (!targetDir) {
            showModal('Percorso mancante', 'Specifica il percorso della cartella dei salvataggi del gioco.');
            return;
        }

        const doBackup = backupCheckbox.checked;
        btnInstall.disabled = true;
        btnInstall.innerHTML = 'Installazione in corso...';

        try {
            const res = await fetch('/api/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    target_dir: targetDir,
                    backup: doBackup
                })
            });

            const data = await res.json();
            if (data.success) {
                let msg = `<p>Salvataggi installati correttamente nella cartella di gioco!</p>`;
                msg += `<p>File installati: <strong>${data.installed_files.join(', ')}</strong></p>`;
                if (data.backup_folder) {
                    msg += `<p style="margin-top:10px;">🛡️ <strong>Backup creato in:</strong><br><code>${escapeHtml(data.backup_folder)}</code></p>`;
                }
                const currentG = (gameSelect ? gameSelect.value : '');
                if (currentG === 'hogwarts-legacy') {
                    msg += `<p style="margin-top:10px; color:#4ade80;">💡 L'indice <code>SaveGameList.sav</code> è stato aggiornato: Hogwarts Legacy ricaricherà automaticamente tutti i nuovi slot nel menu!</p>`;
                }
                showModal('Operazione completata con successo!', msg);
            } else {
                showModal('Errore di installazione', data.error || 'Impossibile scrivere nella cartella specificata.');
            }
        } catch (e) {
            showModal('Errore', e.message);
        } finally {
            btnInstall.disabled = false;
            btnInstall.innerHTML = `
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <span>Installa Direttamente nella Cartella di Gioco</span>
            `;
        }
    });

    // Reset button
    btnReset.addEventListener('click', () => {
        currentSessionId = null;
        fileInput.value = '';
        localPathInput.value = '';
        resultSection.style.display = 'none';
        uploadSection.style.display = 'block';
    });

    // Modal handlers
    function showModal(title, htmlBody) {
        modalTitle.textContent = title;
        modalBody.innerHTML = htmlBody;
        modalBackdrop.style.display = 'flex';
    }

    function closeModal() {
        modalBackdrop.style.display = 'none';
    }

    modalClose.addEventListener('click', closeModal);
    modalConfirm.addEventListener('click', closeModal);
    modalBackdrop.addEventListener('click', (e) => {
        if (e.target === modalBackdrop) closeModal();
    });

    function showProgress(text) {
        progressLabel.textContent = text;
        progressContainer.style.display = 'block';
    }

    function hideProgress() {
        progressContainer.style.display = 'none';
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Auto-detect game paths on system
    async function loadDetectedPaths(gameId) {
        const game = gameId || (gameSelect ? gameSelect.value : 'hogwarts-legacy');
        try {
            const res = await fetch(`/api/detect-paths?game=${encodeURIComponent(game)}`);
            const data = await res.json();
            if (data.success && data.paths && data.paths.length > 0) {
                detectedPaths = data.paths;
                detectedFoldersBox.style.display = 'block';
                detectedList.innerHTML = '';

                data.paths.forEach((p, idx) => {
                    const item = document.createElement('div');
                    item.className = 'detected-item' + (idx === 0 ? ' selected' : '');
                    item.innerHTML = `
                        <div class="detected-info">
                            <div class="detected-type">${escapeHtml(p.type || p.platform || 'Cartella Rilevata')}</div>
                            <div class="detected-path">${escapeHtml(p.path)}</div>
                        </div>
                        <span class="detected-badge">Seleziona</span>
                    `;

                    item.addEventListener('click', () => {
                        targetDirInput.value = p.path;
                        detectedList.querySelectorAll('.detected-item').forEach(el => el.classList.remove('selected'));
                        item.classList.add('selected');
                    });

                    detectedList.appendChild(item);
                });

                if (data.paths[0]) {
                    targetDirInput.value = data.paths[0].path;
                }
            } else {
                detectedFoldersBox.style.display = 'none';
            }
        } catch (e) {
            console.warn('Rilevamento percorsi locali fallito:', e);
            detectedFoldersBox.style.display = 'none';
        }
    }

    // Init
    loadGames();
    loadDetectedPaths();
});
