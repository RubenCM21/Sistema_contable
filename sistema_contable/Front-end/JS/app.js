// ============================================================
// JS/app.js — ContaFlow
// ============================================================

const state = {
  backendOnline: false,
  selectedFile:  null,
  procesado:     false,
  mic: { active: false, recognition: null, supported: false, dictatedText: '' }
};

// ── DOM refs ──────────────────────────────────────────────────
const sidebar       = document.getElementById('sidebar');
const menuToggle    = document.getElementById('menu-toggle');
const navItems      = document.querySelectorAll('.nav-item[data-section]');
const topbarTitle   = document.getElementById('topbar-title');
const loader        = document.getElementById('loader');
const toast         = document.getElementById('toast');
const fileInput     = document.getElementById('file-input');
const fileDisplay   = document.getElementById('file-name-display');
const fileNameText  = document.getElementById('file-name-text');
const charCount     = document.getElementById('char-count');
const textInput     = document.getElementById('text-input');
const resultPreview = document.getElementById('result-preview');
const statusDot     = document.getElementById('status-dot');
const dropZone      = document.getElementById('drop-zone');
const btnMic        = document.getElementById('btn-mic');
const btnMicStop    = document.getElementById('btn-mic-stop');
const micIcon       = document.getElementById('mic-icon');
const micLabel      = document.getElementById('mic-label');
const micStatusText = document.getElementById('mic-status-text');
const micStatusBadge= document.getElementById('mic-status-badge');
const micVisualizer = document.getElementById('mic-visualizer');
const micInterim    = document.getElementById('mic-interim');
const micInterimText= document.getElementById('mic-interim-text');
const micBrowserWarn= document.getElementById('mic-browser-warning');
const micSection    = document.getElementById('mic-section');
const micLang       = document.getElementById('mic-lang');
const btnClearDic   = document.getElementById('btn-mic-clear-text');

const TITLES = {
  upload:    'Cargar Enunciado',
  diario:    'Libro Diario',
  mayor:     'Libro Mayor',
  balance:   'Balance de Comprobación',
  situacion: 'Estado de Situación Financiera',
  resultados:'Estado de Resultados',
};

// ── INIT ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await pingBackend();
  initMic();
  bindEvents();
});

// ── HEALTH ────────────────────────────────────────────────────
async function pingBackend() {
  const ok = await checkBackendHealth();
  state.backendOnline = ok;
  const dot = statusDot.querySelector('.dot');
  const txt = statusDot.querySelector('span:last-child');
  dot.className  = ok ? 'dot dot-green' : 'dot dot-red';
  txt.textContent = ok ? 'Backend conectado' : 'Backend desconectado';
  if (!ok) showToast('⚠ No se pudo conectar al backend en localhost:8000', 'err');
}

// ── MIC ───────────────────────────────────────────────────────
function initMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    state.mic.supported = false;
    if (micBrowserWarn) micBrowserWarn.style.display = 'flex';
    if (btnMic) { btnMic.disabled = true; btnMic.style.opacity = '0.4'; btnMic.style.cursor = 'not-allowed'; }
    setMicStatus('No disponible en este navegador', 'idle');
    return;
  }
  state.mic.supported = true;
  const rec = new SR();
  rec.continuous = true; rec.interimResults = true; rec.maxAlternatives = 1;
  rec.lang = micLang?.value || 'es-PE';

  rec.onresult = (e) => {
    let interim = '', final = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      e.results[i].isFinal ? (final += t + ' ') : (interim += t);
    }
    if (micInterim) { micInterim.style.display = interim ? 'flex' : 'none'; if (micInterimText) micInterimText.textContent = interim; }
    if (final) {
      const cur = textInput.value;
      const sep = cur && !cur.endsWith(' ') && !cur.endsWith('\n') ? ' ' : '';
      textInput.value = cur + sep + final;
      state.mic.dictatedText += sep + final;
      charCount.textContent = textInput.value.length;
      textInput.scrollTop = textInput.scrollHeight;
      if (btnClearDic) btnClearDic.style.display = 'flex';
    }
  };
  rec.onstart = () => {
    state.mic.active = true;
    micSection?.classList.add('mic-active-state');
    textInput.classList.add('recording');
    btnMic?.classList.add('recording');
    if (micLabel) micLabel.textContent = 'Grabando...';
    if (micVisualizer) micVisualizer.style.display = 'flex';
    if (btnMicStop) btnMicStop.style.display = 'flex';
    setMicStatus('Escuchando...', 'recording');
  };
  rec.onend = () => {
    if (state.mic.active) { try { rec.start(); } catch(e){} return; }
    stopMicUI();
  };
  rec.onerror = (e) => {
    if (['not-allowed','permission-denied'].includes(e.error)) {
      showToast('Permiso de micrófono denegado.', 'err'); setMicStatus('Permiso denegado', 'idle');
    } else if (e.error === 'audio-capture') {
      showToast('No se detectó micrófono.', 'err'); state.mic.active = false; stopMicUI();
    }
  };
  state.mic.recognition = rec;
  micLang?.addEventListener('change', () => { rec.lang = micLang.value; });
}

function toggleMic() { if (!state.mic.supported) { showToast('Usa Chrome o Edge.', 'err'); return; } state.mic.active ? stopMic() : startMic(); }
function startMic()  { if (!state.mic.recognition) return; if (micLang) state.mic.recognition.lang = micLang.value; state.mic.active = true; try { state.mic.recognition.start(); } catch(e){} }
function stopMic()   { if (!state.mic.recognition) return; state.mic.active = false; state.mic.recognition.stop(); stopMicUI(); }
function stopMicUI() {
  state.mic.active = false;
  micSection?.classList.remove('mic-active-state');
  textInput.classList.remove('recording');
  btnMic?.classList.remove('recording');
  if (micLabel) micLabel.textContent = 'Activar Micrófono';
  if (micVisualizer) micVisualizer.style.display = 'none';
  if (btnMicStop) btnMicStop.style.display = 'none';
  if (micInterim) micInterim.style.display = 'none';
  setMicStatus('Listo para grabar', 'idle');
}
function setMicStatus(text, type) {
  if (micStatusText) micStatusText.textContent = text;
  const dot = micStatusBadge?.querySelector('.mic-dot');
  if (dot) { dot.className = 'mic-dot'; dot.classList.add(type === 'recording' ? 'mic-dot-recording' : type === 'ok' ? 'mic-dot-ok' : 'mic-dot-idle'); }
}

// ── EVENTS ────────────────────────────────────────────────────
function bindEvents() {
  navItems.forEach(item => item.addEventListener('click', (e) => { e.preventDefault(); showSection(item.dataset.section); }));
  menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', (e) => { if (window.innerWidth <= 768 && !sidebar.contains(e.target) && e.target !== menuToggle) sidebar.classList.remove('open'); });

  fileInput.addEventListener('change', (e) => { if (e.target.files[0]) selectFile(e.target.files[0]); });
  dropZone.addEventListener('dragover',  (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
  dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('dragover'));
  dropZone.addEventListener('drop', (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); if (e.dataTransfer.files[0]) selectFile(e.dataTransfer.files[0]); });

  textInput.addEventListener('input', () => { charCount.textContent = textInput.value.length; });
  document.getElementById('btn-process').addEventListener('click', procesarEnunciado);
  document.getElementById('btn-generate-all').addEventListener('click', generarTodo);
  document.getElementById('btn-generate-all-2').addEventListener('click', generarTodo);
  document.getElementById('btn-export-excel').addEventListener('click', (e) => { e.preventDefault(); exportar('excel', null); });
  document.getElementById('btn-export-pdf').addEventListener('click',   (e) => { e.preventDefault(); exportar('pdf', null); });

  if (btnMic)    btnMic.addEventListener('click', toggleMic);
  if (btnMicStop)btnMicStop.addEventListener('click', stopMic);
  if (btnClearDic) btnClearDic.addEventListener('click', () => {
    textInput.value = textInput.value.replace(state.mic.dictatedText, '').trimEnd();
    state.mic.dictatedText = ''; charCount.textContent = textInput.value.length;
    btnClearDic.style.display = 'none'; showToast('Texto dictado eliminado', 'info');
  });
  const btnClearAll = document.getElementById('btn-clear-text');
  if (btnClearAll) btnClearAll.addEventListener('click', () => {
    textInput.value = ''; state.mic.dictatedText = ''; charCount.textContent = '0';
    if (btnClearDic) btnClearDic.style.display = 'none';
  });
  window.addEventListener('beforeunload', () => { if (state.mic.active) stopMic(); });
}

// ── NAVIGATION ────────────────────────────────────────────────
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById(`section-${name}`)?.classList.add('active');
  topbarTitle.textContent = TITLES[name] || name;
  navItems.forEach(item => item.classList.toggle('active', item.dataset.section === name));
  if (name !== 'upload') loadSection(name);
  if (window.innerWidth <= 768) sidebar.classList.remove('open');
}

// ── LOAD SECTION ──────────────────────────────────────────────
async function loadSection(name) {
  _showSkeleton(name);
  try {
    switch (name) {
      case 'diario': {
        const data = await apiGetLibroDiario();
        // Backend retorna { total_registros, resumen, datos: [...] }
        // renderLibroDiario espera el array de filas directamente
        renderLibroDiario(data.datos || []);
        break;
      }
      case 'mayor': {
        const data = await apiGetLibroMayor();
        // Backend retorna { total_cuentas, cuentas: [...] }
        renderLibroMayor(data.cuentas || []);
        break;
      }
      case 'balance': {
        const data = await apiGetBalance();
        renderBalance(data);
        break;
      }
      case 'situacion': {
        const data = await apiGetESF();
        renderESF(data);
        break;
      }
      case 'resultados': {
        const data = await apiGetER();
        renderEstadoResultados(data);
        break;
      }
    }
  } catch (err) {
    _showError(name, err.message);
    showToast(`Error al cargar ${TITLES[name]}: ${err.message}`, 'err');
  }
}

function _showSkeleton(name) {
  const ids = { diario:'table-diario', mayor:'mayor-container', balance:'table-balance', situacion:'situacion-container', resultados:'resultados-container' };
  const el = document.getElementById(ids[name]);
  if (el) el.innerHTML = `<div class="skeleton-loader"><div class="sk-row"></div><div class="sk-row sk-short"></div><div class="sk-row"></div><div class="sk-row sk-short"></div><div class="sk-row"></div></div>`;
}

function _showError(name, msg) {
  const ids = { diario:'table-diario', mayor:'mayor-container', balance:'table-balance', situacion:'situacion-container', resultados:'resultados-container' };
  const el = document.getElementById(ids[name]);
  if (el) el.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><p>Error al cargar datos</p><small>${msg}</small></div>`;
}

// ── SELECT FILE ───────────────────────────────────────────────
function selectFile(file) {
  state.selectedFile = file;
  fileNameText.textContent = file.name;
  fileDisplay.style.display = 'flex';
  showToast(`Archivo: ${file.name}`, 'info');
}

// ── PROCESS ───────────────────────────────────────────────────
async function procesarEnunciado() {
  const texto = textInput.value.trim();
  const file  = state.selectedFile;

  if (!texto && !file) { showToast('Escribe un enunciado o sube un archivo.', 'err'); return; }
  if (!state.backendOnline) { showToast('Backend no conectado en localhost:8000', 'err'); return; }
  if (state.mic.active) { stopMic(); await delay(300); }

  showLoader();
  try {
    let resultado;
    activateStep(1); await delay(400);

    if (file) {
      resultado = await apiProcesarArchivo(file);
    } else {
      resultado = await apiProcesarTexto(texto);
    }

    activateStep(2); await delay(500);
    activateStep(3); await delay(400);
    activateStep(4); await delay(300);

    hideLoader();
    mostrarResultado(resultado);
    state.procesado = true;

  } catch (err) {
    hideLoader();
    showToast(`Error al procesar: ${err.message}`, 'err');
  }
}

// ── MOSTRAR RESULTADO ─────────────────────────────────────────
function mostrarResultado(respuesta) {
  resultPreview.style.display = 'block';
  resultPreview.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // El backend /interpretar retorna:
  // { interpretacion: { asientos: [...], total_asientos }, guardado, detalle_guardado }
  // El backend /api/procesar-archivo retorna:
  // { interpretacion: { asientos: [...], total_asientos }, guardado, ... }
  const interp = respuesta?.interpretacion || respuesta;
  const asientos = interp?.asientos || [];
  const total    = interp?.total_asientos ?? asientos.length;

  let partidas = 0;
  asientos.forEach(a => { partidas += (a.partidas || []).length; });

  const descuadrados = asientos.filter(a => a.cuadrado === false).length;

  document.getElementById('result-stats').innerHTML = `
    <div class="stat-card">
      <div class="stat-num">${total}</div>
      <div class="stat-lbl">Asientos registrados</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">${partidas}</div>
      <div class="stat-lbl">Partidas contables</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" style="color:${descuadrados > 0 ? 'var(--accent-red)' : 'var(--accent-green-l)'}">
        ${descuadrados}
      </div>
      <div class="stat-lbl">Asientos descuadrados</div>
    </div>`;

  showToast('¡Enunciado procesado correctamente!', 'ok');
}

// ── GENERAR TODO ──────────────────────────────────────────────
async function generarTodo() {
  showLoader('Generando sistema contable completo...');
  const sections = ['diario', 'mayor', 'balance', 'situacion', 'resultados'];
  try {
    for (let i = 0; i < sections.length; i++) {
      activateStep(i + 1);
      await loadSection(sections[i]);
      await delay(200);
    }
    hideLoader();
    showToast('Sistema contable generado completamente', 'ok');
    showSection('diario');
  } catch (err) {
    hideLoader();
    showToast('Error al generar el sistema: ' + err.message, 'err');
  }
}

// ── EXPORT ────────────────────────────────────────────────────
async function exportar(tipo, tabla) {
  if (!state.backendOnline) { showToast('Backend no conectado', 'err'); return; }
  showToast(`Generando ${tipo.toUpperCase()}...`, 'info');
  try {
    const tablas = tabla ? [tabla] : null;
    tipo === 'excel' ? await apiExportarExcel(tablas) : await apiExportarPDF(tablas);
    showToast(`${tipo.toUpperCase()} descargado exitosamente`, 'ok');
  } catch (err) {
    showToast('Error al exportar: ' + err.message, 'err');
  }
}

// ── LOADER ────────────────────────────────────────────────────
function showLoader(text = 'Interpretando enunciado con IA...') {
  loader.style.display = 'flex';
  document.getElementById('loader-text').textContent = text;
  for (let i = 1; i <= 4; i++) {
    const s = document.getElementById(`step${i}`);
    s.className = 'step';
    s.querySelector('i').className = 'fa-solid fa-circle';
  }
}
function hideLoader() { loader.style.display = 'none'; }
function activateStep(n) {
  if (n > 1) {
    const p = document.getElementById(`step${n-1}`);
    if (p) { p.classList.remove('active'); p.classList.add('done'); p.querySelector('i').className = 'fa-solid fa-check'; }
  }
  const c = document.getElementById(`step${n}`);
  if (c) { c.classList.add('active'); c.querySelector('i').className = 'fa-solid fa-circle-notch fa-spin'; }
}

// ── TOAST ─────────────────────────────────────────────────────
let toastTimer = null;
function showToast(message, type = 'info') {
  if (toastTimer) clearTimeout(toastTimer);
  toast.textContent = message;
  toast.className = `toast toast-${type} show`;
  toastTimer = setTimeout(() => toast.classList.remove('show'), 4000);
}

const delay = (ms) => new Promise(r => setTimeout(r, ms));