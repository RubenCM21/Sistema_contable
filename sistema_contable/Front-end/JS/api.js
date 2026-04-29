// ============================================================
// JS/api.js — ContaFlow
// ============================================================

const API_BASE = 'http://localhost:8000';

async function apiFetch(endpoint, options = {}) {
  try {
    const res = await fetch(API_BASE + endpoint, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    console.error('[API Error]', endpoint, e.message);
    throw e;
  }
}

async function apiFetchBlob(endpoint, options = {}) {
  const res = await fetch(API_BASE + endpoint, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return await res.blob();
}

// ── Health ────────────────────────────────────────────────────
async function checkBackendHealth() {
  try { await apiFetch('/health'); return true; }
  catch { return false; }
}

// ── Procesar texto  → POST /interpretar ──────────────────────
async function apiProcesarTexto(texto) {
  return apiFetch('/interpretar', {
    method: 'POST',
    body: JSON.stringify({ texto, guardar: true }),
  });
}

// ── Procesar archivo  → POST /api/procesar-archivo ───────────
async function apiProcesarArchivo(file) {
  const formData = new FormData();
  formData.append('archivo', file);
  return apiFetch('/api/procesar-archivo', {
    method: 'POST',
    headers: {},
    body: formData,
  });
}

// ── Libro Diario  → GET /diario ───────────────────────────────
// Retorna: { total_registros, resumen, datos: [...] }
async function apiGetLibroDiario(params = {}) {
  const q = _qs(_clean(params));
  return apiFetch(`/diario${q}`);
}

// ── Libro Mayor  → GET /mayor ─────────────────────────────────
// Retorna: { total_cuentas, cuentas: [...] }
async function apiGetLibroMayor(codCuenta = null) {
  return apiFetch(codCuenta ? `/mayor/${codCuenta}` : '/mayor');
}

// ── Balance  → GET /balance ───────────────────────────────────
// Retorna: { periodo, detalle:[...], total_debe, total_haber, estado }
async function apiGetBalance(params = {}) {
  const q = _qs(_clean(params));
  return apiFetch(`/balance${q}`);
}

// ── ESF  → GET /situacion ─────────────────────────────────────
async function apiGetESF(params = {}) {
  const q = _qs(_clean(params));
  return apiFetch(`/situacion${q}`);
}

// ── Estado de Resultados  → GET /resultados ───────────────────
async function apiGetER(params = {}) {
  const q = _qs(_clean(params));
  return apiFetch(`/resultados${q}`);
}

// ── Exportar Excel ────────────────────────────────────────────
async function apiExportarExcel(tablas = null) {
  const q = tablas ? `?tablas=${tablas.join(',')}` : '';
  const blob = await apiFetchBlob(`/exportar/excel${q}`);
  _download(blob, 'sistema_contable.xlsx');
}

// ── Exportar PDF ──────────────────────────────────────────────
async function apiExportarPDF(tablas = null) {
  const q = tablas ? `?tablas=${tablas.join(',')}` : '';
  const blob = await apiFetchBlob(`/exportar/pdf${q}`);
  _download(blob, 'sistema_contable.pdf');
}

// ── Helpers ───────────────────────────────────────────────────
function _clean(params) {
  const out = {};
  for (const [k, v] of Object.entries(params))
    if (v !== null && v !== undefined && v !== '') out[k] = v;
  return out;
}
function _qs(params) {
  const q = new URLSearchParams(params).toString();
  return q ? '?' + q : '';
}
function _download(blob, nombre) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = nombre;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
}