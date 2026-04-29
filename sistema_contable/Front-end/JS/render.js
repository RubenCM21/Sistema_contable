// ============================================================
// JS/render.js — ContaFlow
// Estructuras que llegan del backend:
//   /diario     → { datos:[{cod_asiento,fecha,glosa,cod_cuenta,nombre_cuenta,tipo_movimiento,debe,haber}] }
//   /mayor      → { cuentas:[{cod_cuenta,nombre_cuenta,naturaleza,total_debe,total_haber,saldo_final,movimientos:[...]}] }
//   /balance    → { periodo,detalle:[{cod_cuenta,nombre_cuenta,debe,haber}],total_debe,total_haber,estado }
//   /situacion  → { fecha_corte,activo:{corriente,no_corriente,...},pasivo:{...},patrimonio:{...},cuadrado,... }
//   /resultados → { periodo,ingresos,costo_ventas,utilidad_bruta,...,utilidad_neta,resultado }
// ============================================================

const fmt = (n) => {
  if (n === null || n === undefined || n === '') return '—';
  return 'S/ ' + Number(n).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const fmtNum = (n) => {
  if (n === null || n === undefined) return '';
  return Number(n).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

// ════════════════════════════════════════════════════════════
// LIBRO DIARIO
// Recibe: array de filas (ya extraído de data.datos en app.js)
// ════════════════════════════════════════════════════════════
function renderLibroDiario(rows) {
  const container = document.getElementById('table-diario');
  const totalsEl  = document.getElementById('totals-diario');

  if (!rows || rows.length === 0) {
    container.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-book"></i>
      <p>No hay asientos registrados</p>
      <small>Carga y procesa un enunciado primero</small>
    </div>`;
    if (totalsEl) totalsEl.style.display = 'none';
    return;
  }

  let totalDebe = 0, totalHaber = 0, lastAsiento = null;
  let html = '';

  rows.forEach((row, i) => {
    const isNew = row.cod_asiento !== lastAsiento;
    lastAsiento = row.cod_asiento;

    const debe  = row.debe  > 0 ? `<span class="cell-debe">${fmtNum(row.debe)}</span>`   : `<span class="cell-empty">—</span>`;
    const haber = row.haber > 0 ? `<span class="cell-haber">${fmtNum(row.haber)}</span>` : `<span class="cell-empty">—</span>`;
    const badge = row.tipo_movimiento === 'D' ? `<span class="badge-d">D</span>` : `<span class="badge-h">H</span>`;

    totalDebe  += row.debe  || 0;
    totalHaber += row.haber || 0;

    html += `<tr class="${isNew && i > 0 ? 'border-top-accent' : ''}">
      <td class="td-code">${row.cod_asiento ?? '—'}</td>
      <td class="td-date">${row.fecha ?? '—'}</td>
      <td class="td-glosa">${row.glosa ?? ''}</td>
      <td class="td-code">${row.cod_cuenta ?? '—'}</td>
      <td>${row.nombre_cuenta ?? '—'}</td>
      <td>${badge}</td>
      <td class="td-num">${debe}</td>
      <td class="td-num">${haber}</td>
    </tr>`;
  });

  html += `<tr class="row-total">
    <td colspan="6">TOTALES</td>
    <td class="td-num">${fmtNum(totalDebe)}</td>
    <td class="td-num">${fmtNum(totalHaber)}</td>
  </tr>`;

  container.innerHTML = `
    <div class="table-scroll">
      <table class="data-table">
        <thead><tr>
          <th>#</th><th>Fecha</th><th>Glosa</th>
          <th>Cta.</th><th>Nombre de Cuenta</th>
          <th>D/H</th><th>DEBE (S/)</th><th>HABER (S/)</th>
        </tr></thead>
        <tbody>${html}</tbody>
      </table>
    </div>`;

  if (totalsEl) {
    const ok = Math.round(totalDebe * 100) === Math.round(totalHaber * 100);
    totalsEl.style.display = 'flex';
    totalsEl.innerHTML = `
      <div class="total-chip chip-debe"><i class="fa-solid fa-arrow-right"></i> TOTAL DEBE: ${fmtNum(totalDebe)}</div>
      <div class="total-chip chip-haber"><i class="fa-solid fa-arrow-left"></i> TOTAL HABER: ${fmtNum(totalHaber)}</div>
      <div class="total-chip ${ok ? 'chip-ok' : 'chip-err'}">
        <i class="fa-solid fa-${ok ? 'check-circle' : 'triangle-exclamation'}"></i>
        ${ok ? 'CUADRADO' : 'DESCUADRADO'}
      </div>`;
  }
}

// ════════════════════════════════════════════════════════════
// LIBRO MAYOR
// Recibe: array de cuentas (ya extraído de data.cuentas en app.js)
// ════════════════════════════════════════════════════════════
function renderLibroMayor(cuentas) {
  const container = document.getElementById('mayor-container');

  if (!cuentas || cuentas.length === 0) {
    container.innerHTML = `<div class="card"><div class="empty-state">
      <i class="fa-solid fa-book-open"></i>
      <p>No hay movimientos en el mayor</p>
      <small>Carga y procesa un enunciado primero</small>
    </div></div>`;
    return;
  }

  container.innerHTML = `<div class="mayor-grid">${cuentas.map(_renderCuentaMayor).join('')}</div>`;

  // Collapse/expand
  container.querySelectorAll('.mayor-account-header').forEach(h => {
    h.addEventListener('click', () => {
      const body    = h.nextElementSibling;
      const chevron = h.querySelector('.chevron');
      const isOpen  = body.style.maxHeight && body.style.maxHeight !== '0px';
      body.style.maxHeight = isOpen ? '0px' : body.scrollHeight + 'px';
      chevron.classList.toggle('open', !isOpen);
    });
  });

  // Abrir la primera
  const first = container.querySelector('.collapsible-body');
  if (first) {
    first.style.maxHeight = first.scrollHeight + 'px';
    container.querySelector('.chevron')?.classList.add('open');
  }
}

function _renderCuentaMayor(cuenta) {
  const isDeudor   = cuenta.naturaleza === 'DEUDOR';
  const saldoClass = isDeudor ? 'saldo-deudor' : 'saldo-acreedor';
  const saldoLabel = isDeudor ? 'Saldo D' : 'Saldo H';
  const movs       = cuenta.movimientos || [];

  let rows = movs.map(m => {
    const debe  = m.debe  > 0 ? `<span class="cell-debe">${fmtNum(m.debe)}</span>`   : `<span class="cell-empty">—</span>`;
    const haber = m.haber > 0 ? `<span class="cell-haber">${fmtNum(m.haber)}</span>` : `<span class="cell-empty">—</span>`;
    return `<tr>
      <td class="td-date">${m.fecha ?? '—'}</td>
      <td class="td-glosa">${m.glosa ?? ''}</td>
      <td class="td-num">${debe}</td>
      <td class="td-num">${haber}</td>
      <td class="td-num" style="font-family:var(--font-mono);font-size:13px">${fmtNum(m.saldo_acumulado)}</td>
    </tr>`;
  }).join('');

  rows += `<tr class="row-total">
    <td colspan="2">TOTALES</td>
    <td class="td-num">${fmtNum(cuenta.total_debe)}</td>
    <td class="td-num">${fmtNum(cuenta.total_haber)}</td>
    <td class="td-num">${fmtNum(cuenta.saldo_final)}</td>
  </tr>`;

  return `
    <div class="mayor-account-card">
      <div class="mayor-account-header">
        <div class="mayor-account-title">
          <span class="mayor-code">${cuenta.cod_cuenta}</span>
          <span class="mayor-name">${cuenta.nombre_cuenta}</span>
        </div>
        <div class="mayor-badges">
          <span class="saldo-badge ${saldoClass}">${saldoLabel}: ${fmtNum(cuenta.saldo_final)}</span>
          <i class="fa-solid fa-chevron-down chevron"></i>
        </div>
      </div>
      <div class="collapsible-body" style="max-height:0px">
        <div class="table-scroll">
          <table class="data-table">
            <thead><tr>
              <th>Fecha</th><th>Descripción</th>
              <th>DEBE (S/)</th><th>HABER (S/)</th><th>Saldo Acum.</th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    </div>`;
}

// ════════════════════════════════════════════════════════════
// BALANCE DE COMPROBACIÓN
// Recibe: objeto completo del backend
// ════════════════════════════════════════════════════════════
function renderBalance(data) {
  const container = document.getElementById('table-balance');
  const checkEl   = document.getElementById('balance-check');

  if (!data || !data.detalle || data.detalle.length === 0) {
    container.innerHTML = `<div class="empty-state">
      <i class="fa-solid fa-scale-balanced"></i>
      <p>Sin datos de balance</p>
      <small>Carga y procesa un enunciado primero</small>
    </div>`;
    if (checkEl) checkEl.style.display = 'none';
    return;
  }

  let html = data.detalle.map(row => {
    const debe  = row.debe  > 0 ? fmtNum(row.debe)  : '—';
    const haber = row.haber > 0 ? fmtNum(row.haber) : '—';
    return `<tr>
      <td class="td-code">${row.cod_cuenta}</td>
      <td>${row.nombre_cuenta}</td>
      <td class="td-num ${row.debe  > 0 ? 'cell-debe'  : 'cell-empty'}">${debe}</td>
      <td class="td-num ${row.haber > 0 ? 'cell-haber' : 'cell-empty'}">${haber}</td>
    </tr>`;
  }).join('');

  html += `<tr class="row-total">
    <td colspan="2">TOTALES</td>
    <td class="td-num">${fmtNum(data.total_debe)}</td>
    <td class="td-num">${fmtNum(data.total_haber)}</td>
  </tr>`;

  container.innerHTML = `
    <div class="period-info">
      <i class="fa-solid fa-calendar"></i> Período: <strong>${data.periodo ?? '—'}</strong>
    </div>
    <div class="table-scroll">
      <table class="data-table">
        <thead><tr>
          <th>Código</th><th>Nombre de Cuenta</th>
          <th>DEBE (S/)</th><th>HABER (S/)</th>
        </tr></thead>
        <tbody>${html}</tbody>
      </table>
    </div>`;

  if (checkEl) {
    const ok = data.estado === 'CUADRADO';
    checkEl.style.display = 'flex';
    checkEl.className = `balance-check-box ${ok ? 'balance-ok' : 'balance-err'}`;
    checkEl.innerHTML = `
      <i class="fa-solid fa-${ok ? 'check-circle' : 'triangle-exclamation'}" style="font-size:20px"></i>
      <div>
        <strong>${ok ? '✓ Balance CUADRADO' : '✗ Balance DESCUADRADO'}</strong>
        <div style="font-size:12px;font-weight:400;margin-top:2px">
          Debe: ${fmt(data.total_debe)} &nbsp;|&nbsp; Haber: ${fmt(data.total_haber)}
          ${!ok ? `&nbsp;|&nbsp; Diferencia: ${fmt(Math.abs((data.total_debe||0)-(data.total_haber||0)))}` : ''}
        </div>
      </div>`;
  }
}

// ════════════════════════════════════════════════════════════
// ESTADO DE SITUACIÓN FINANCIERA
// ════════════════════════════════════════════════════════════
function renderESF(data) {
  const container = document.getElementById('situacion-container');

  if (!data || data.error) {
    container.innerHTML = `<div class="card"><div class="empty-state">
      <i class="fa-solid fa-building-columns"></i>
      <p>Sin datos disponibles</p>
      <small>${data?.error ?? 'Carga y procesa un enunciado primero'}</small>
    </div></div>`;
    return;
  }

  const rows = (items = []) => (items || []).map(i =>
    `<div class="esf-row">
      <span>${i.nombre_cuenta}</span>
      <span class="esf-val">${fmt(i.valor)}</span>
    </div>`
  ).join('');

  const resultadoEjercicio = data.patrimonio?.resultado_ejercicio ?? 0;
  const colorResultado = resultadoEjercicio >= 0 ? 'var(--accent-green-l)' : '#ff6b6b';

  container.innerHTML = `
    <div class="esf-date-info">
      <i class="fa-solid fa-calendar"></i> Al <strong>${data.fecha_corte ?? '—'}</strong>
    </div>
    <div class="esf-grid">
      <!-- ACTIVO -->
      <div class="esf-side">
        <div class="esf-side-header activo"><i class="fa-solid fa-coins"></i> ACTIVO</div>

        <div class="esf-section-title">Activo Corriente</div>
        ${rows(data.activo?.corriente)}
        <div class="esf-subtotal">
          <span>Total Activo Corriente</span>
          <span class="esf-val">${fmt(data.activo?.total_corriente)}</span>
        </div>

        <div class="esf-section-title">Activo No Corriente</div>
        ${rows(data.activo?.no_corriente)}
        <div class="esf-subtotal">
          <span>Total Activo No Corriente</span>
          <span class="esf-val">${fmt(data.activo?.total_no_corriente)}</span>
        </div>

        <div class="esf-total-bar">
          <span>TOTAL ACTIVO</span>
          <span class="esf-val">${fmt(data.activo?.total_activo)}</span>
        </div>
      </div>

      <!-- PASIVO Y PATRIMONIO -->
      <div class="esf-side">
        <div class="esf-side-header pasivo"><i class="fa-solid fa-landmark"></i> PASIVO Y PATRIMONIO</div>

        <div class="esf-section-title">Pasivo Corriente</div>
        ${rows(data.pasivo?.corriente)}
        <div class="esf-subtotal">
          <span>Total Pasivo Corriente</span>
          <span class="esf-val">${fmt(data.pasivo?.total_corriente)}</span>
        </div>

        <div class="esf-section-title">Pasivo No Corriente</div>
        ${rows(data.pasivo?.no_corriente)}
        <div class="esf-subtotal">
          <span>Total Pasivo No Corriente</span>
          <span class="esf-val">${fmt(data.pasivo?.total_no_corriente)}</span>
        </div>

        <div class="esf-section-title">Patrimonio</div>
        ${rows(data.patrimonio?.detalle)}
        <div class="esf-row">
          <span>Resultado del Ejercicio</span>
          <span class="esf-val" style="color:${colorResultado}">${fmt(resultadoEjercicio)}</span>
        </div>
        <div class="esf-subtotal">
          <span>Total Patrimonio</span>
          <span class="esf-val">${fmt((data.patrimonio?.total_patrimonio ?? 0) + resultadoEjercicio)}</span>
        </div>

        <div class="esf-total-bar">
          <span>TOTAL PASIVO + PATRIMONIO</span>
          <span class="esf-val">${fmt(data.total_pasivo_patrimonio)}</span>
        </div>
      </div>
    </div>

    <div class="balance-check-box esf-check ${data.cuadrado ? 'balance-ok' : 'balance-err'}">
      <i class="fa-solid fa-${data.cuadrado ? 'check-circle' : 'triangle-exclamation'}" style="font-size:20px"></i>
      <div>
        <strong>${data.cuadrado ? '✓ El Estado de Situación Financiera CUADRA' : '✗ No cuadra — revisa los asientos'}</strong>
        ${!data.cuadrado ? `<div style="font-size:12px;margin-top:2px">Diferencia: ${fmt(Math.abs(data.diferencia ?? 0))}</div>` : ''}
      </div>
    </div>`;
}

// ════════════════════════════════════════════════════════════
// ESTADO DE RESULTADOS
// ════════════════════════════════════════════════════════════
function renderEstadoResultados(data) {
  const container = document.getElementById('resultados-container');

  if (!data || data.error) {
    container.innerHTML = `<div class="card"><div class="empty-state">
      <i class="fa-solid fa-chart-pie"></i>
      <p>Sin datos disponibles</p>
      <small>${data?.error ?? 'Carga y procesa un enunciado primero'}</small>
    </div></div>`;
    return;
  }

  const esUtil = data.resultado === 'UTILIDAD';

  const row = (label, value, cls = '') =>
    `<div class="er-row ${cls}"><span>${label}</span><span class="er-val">${fmt(value)}</span></div>`;
  const sec = (label) =>
    `<div class="er-section">${label}</div>`;
  const sub = (label, value) =>
    `<div class="er-row er-subtotal"><span><strong>${label}</strong></span><span class="er-val">${fmt(value)}</span></div>`;

  const tasa = ((data.impuesto_renta?.tasa ?? 0) * 100).toFixed(1);

  container.innerHTML = `
    <div class="er-container">
      <div class="period-info" style="padding:14px 24px;">
        <i class="fa-solid fa-calendar"></i>
        ${data.periodo?.fecha_inicio ?? '—'} al ${data.periodo?.fecha_fin ?? '—'}
      </div>

      ${sec('INGRESOS')}
      ${row('Ventas Netas / Ingresos por Servicios', data.ingresos?.ventas_netas)}

      ${sec('COSTO DE VENTAS')}
      ${row('(-) Costo de Ventas', data.costo_ventas?.monto, 'er-gasto')}

      ${sub('UTILIDAD BRUTA', data.utilidad_bruta)}

      ${sec('GASTOS OPERATIVOS')}
      ${row('(-) Gastos de Ventas', data.gastos_operativos?.gastos_ventas?.monto, 'er-gasto')}
      ${row('(-) Gastos de Administración', data.gastos_operativos?.gastos_administracion?.monto, 'er-gasto')}

      ${sub('UTILIDAD OPERATIVA', data.utilidad_operativa)}

      ${sec('OTROS INGRESOS / EGRESOS')}
      ${row('(+) Otros Ingresos', data.otros?.otros_ingresos)}
      ${row('(-) Gastos Financieros', data.otros?.gastos_financieros, 'er-gasto')}
      ${row('(+) Ingresos Financieros', data.otros?.ingresos_financieros)}

      ${sub('UTILIDAD ANTES DE IMPUESTOS', data.utilidad_antes_impuestos)}

      ${sec('IMPUESTO A LA RENTA')}
      ${row(`(-) Impuesto a la Renta (${tasa}%)`, data.impuesto_renta?.monto, 'er-gasto')}

      <div class="er-row er-final">
        <span>${data.resultado ?? 'RESULTADO'} NETA DEL PERÍODO</span>
        <span class="er-val ${esUtil ? 'er-utilidad' : 'er-perdida'}">${fmt(data.utilidad_neta)}</span>
      </div>
    </div>`;
}