# ============================================================
# estado_resultados.py
# Sistema Contable - Estado de Resultados
# Corregido: solo cuentas de 2 dígitos según PCGE
# ============================================================
#
#  (+) Ventas Netas                  → cuenta 70
#  (-) Costo de Ventas               → cuenta 69
#  ══════════════════════════════════
#      UTILIDAD BRUTA
#  (-) Gastos de Ventas              → cuenta 95
#  (-) Gastos de Administración      → cuenta 94
#  ══════════════════════════════════
#      UTILIDAD OPERATIVA
#  (+) Otros Ingresos                → cuenta 75
#  (-) Gastos Financieros            → cuenta 67 / 96
#  (+) Ingresos Financieros          → cuenta 77
#  ══════════════════════════════════
#      UTILIDAD ANTES DE IMPUESTOS
#  (-) Impuesto a la Renta (29.5%)
#  ══════════════════════════════════
#      UTILIDAD (PÉRDIDA) NETA
# ============================================================

from conexion_bd import obtener_conexion, cerrar_conexion

TASA_IR = 0.295


def _saldo_cuentas(cursor, codigos: list) -> tuple:
    """
    Suma SALDO_DEBE y SALDO_HABER de una lista de códigos de 2 dígitos.
    Retorna (total_debe, total_haber).
    """
    if not codigos:
        return 0.0, 0.0

    placeholders = ",".join(["?" for _ in codigos])
    cursor.execute(f"""
        SELECT
            ISNULL(SUM(SALDO_DEBE_CUENTA),  0),
            ISNULL(SUM(SALDO_HABER_CUENTA), 0)
        FROM CUENTA
        WHERE COD_CUENTA IN ({placeholders})
          AND COD_CUENTA BETWEEN 10 AND 99
    """, codigos)
    fila = cursor.fetchone()
    return float(fila[0] or 0), float(fila[1] or 0)


def _detalle_cuentas(cursor, codigos: list, naturaleza: str) -> list:
    """
    Retorna el detalle de movimientos de las cuentas indicadas.
    naturaleza: "HABER" → monto = haber - debe / "DEBE" → monto = debe - haber
    """
    if not codigos:
        return []

    placeholders = ",".join(["?" for _ in codigos])
    cursor.execute(f"""
        SELECT COD_CUENTA, NOMBRE_CUENTA, SALDO_DEBE_CUENTA, SALDO_HABER_CUENTA
        FROM CUENTA
        WHERE COD_CUENTA IN ({placeholders})
          AND COD_CUENTA BETWEEN 10 AND 99
          AND (SALDO_DEBE_CUENTA > 0 OR SALDO_HABER_CUENTA > 0)
        ORDER BY COD_CUENTA
    """, codigos)

    filas = cursor.fetchall()
    resultado = []
    for f in filas:
        debe  = float(f[2] or 0)
        haber = float(f[3] or 0)
        monto = round(haber - debe, 2) if naturaleza == "HABER" else round(debe - haber, 2)
        resultado.append({
            "cod_cuenta": f[0],
            "nombre":     f[1],
            "monto":      monto
        })
    return resultado


def obtener_estado_resultados(fecha_inicio: str = None, fecha_fin: str = None) -> dict:
    """
    Genera el Estado de Resultados usando cuentas de 2 dígitos.
    """
    from datetime import date

    if fecha_inicio is None:
        fecha_inicio = f"{date.today().year}-01-01"
    if fecha_fin is None:
        fecha_fin = str(date.today())

    conexion = obtener_conexion()
    if not conexion:
        return {"error": "No se pudo conectar a la BD"}

    try:
        cursor = conexion.cursor()

        # ── 1. VENTAS NETAS (cta 70) ──────────────────────────
        # 70 = Ventas         → saldo normal HABER
        # 74 = Descuentos concedidos → reduce ventas (saldo DEBE)
        debe_70, haber_70 = _saldo_cuentas(cursor, [70])
        debe_74, haber_74 = _saldo_cuentas(cursor, [74])
        ventas_brutas     = round(haber_70 - debe_70, 2)
        descuentos_conc   = round(debe_74  - haber_74, 2)
        ventas_netas      = round(ventas_brutas - descuentos_conc, 2)
        detalle_ventas    = _detalle_cuentas(cursor, [70, 73, 74], "HABER")

        # ── 2. COSTO DE VENTAS (cta 69) ──────────────────────
        debe_69, haber_69 = _saldo_cuentas(cursor, [69])
        costo_ventas      = round(debe_69 - haber_69, 2)
        detalle_cv        = _detalle_cuentas(cursor, [69], "DEBE")

        utilidad_bruta = round(ventas_netas - costo_ventas, 2)

        # ── 3. GASTOS OPERATIVOS ──────────────────────────────
        # Gastos de Ventas → cuenta analítica 95
        debe_gv, haber_gv = _saldo_cuentas(cursor, [95])
        gastos_ventas     = round(debe_gv - haber_gv, 2)
        detalle_gv        = _detalle_cuentas(cursor, [95], "DEBE")

        # Gastos Administrativos → cuenta analítica 94
        debe_ga, haber_ga = _saldo_cuentas(cursor, [94])
        gastos_admin      = round(debe_ga - haber_ga, 2)
        detalle_ga        = _detalle_cuentas(cursor, [94], "DEBE")

        # Si no hay analíticas, usar cuentas de naturaleza directamente
        # 62 Gastos de Personal, 63 Gastos Servicios, 64 Tributos, 65 Otros
        if gastos_ventas == 0 and gastos_admin == 0:
            debe_op, haber_op = _saldo_cuentas(cursor, [62, 63, 64, 65])
            gastos_admin      = round(debe_op - haber_op, 2)
            detalle_ga        = _detalle_cuentas(cursor, [62, 63, 64, 65], "DEBE")

        utilidad_operativa = round(utilidad_bruta - gastos_ventas - gastos_admin, 2)

        # ── 4. OTROS INGRESOS / EGRESOS ──────────────────────
        # Otros ingresos gestión → 75
        debe_oi, haber_oi = _saldo_cuentas(cursor, [75])
        otros_ingresos    = round(haber_oi - debe_oi, 2)

        # Gastos financieros → 67 o analítica 96
        debe_gf, haber_gf = _saldo_cuentas(cursor, [67, 96])
        gastos_financieros = round(debe_gf - haber_gf, 2)

        # Ingresos financieros → 77
        debe_if, haber_if  = _saldo_cuentas(cursor, [77])
        ingresos_financieros = round(haber_if - debe_if, 2)

        utilidad_antes_ir = round(
            utilidad_operativa
            + otros_ingresos
            - gastos_financieros
            + ingresos_financieros,
            2
        )

        # ── 5. IMPUESTO A LA RENTA ────────────────────────────
        ir = round(max(0, utilidad_antes_ir) * TASA_IR, 2)

        # ── 6. UTILIDAD NETA ──────────────────────────────────
        utilidad_neta = round(utilidad_antes_ir - ir, 2)

        return {
            "periodo": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin":    fecha_fin
            },
            "ingresos": {
                "ventas_brutas": ventas_brutas,
                "ventas_netas":  ventas_netas,
                "detalle":       detalle_ventas,
            },
            "costo_ventas": {
                "monto":   costo_ventas,
                "detalle": detalle_cv
            },
            "utilidad_bruta": utilidad_bruta,
            "gastos_operativos": {
                "gastos_ventas": {
                    "monto":   gastos_ventas,
                    "detalle": detalle_gv
                },
                "gastos_administracion": {
                    "monto":   gastos_admin,
                    "detalle": detalle_ga
                },
                "total_gastos_operativos": round(gastos_ventas + gastos_admin, 2)
            },
            "utilidad_operativa": utilidad_operativa,
            "otros": {
                "otros_ingresos":        otros_ingresos,
                "gastos_financieros":    gastos_financieros,
                "ingresos_financieros":  ingresos_financieros
            },
            "utilidad_antes_impuestos": utilidad_antes_ir,
            "impuesto_renta": {
                "tasa":  TASA_IR,
                "monto": ir
            },
            "utilidad_neta": utilidad_neta,
            "resultado":     "UTILIDAD" if utilidad_neta >= 0 else "PÉRDIDA"
        }

    except Exception as e:
        print(f"[ERROR] obtener_estado_resultados: {e}")
        return {"error": str(e)}
    finally:
        cerrar_conexion(conexion)