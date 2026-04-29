# ============================================================
# estado_situacion_financiera.py
# Sistema Contable - Estado de Situación Financiera
# Corregido: solo cuentas de 2 dígitos según PCGE
# ============================================================

from plan_cuentas import PLAN_CUENTAS
from libro_mayor import obtener_saldos_por_cuenta
from conexion_bd import obtener_conexion, cerrar_conexion


# Clasificación por sección del ESF — SOLO códigos de 2 dígitos
_CLASIFICACION = {
    # ACTIVO CORRIENTE
    10: "activo_corriente",
    11: "activo_corriente",
    12: "activo_corriente",
    13: "activo_corriente",
    14: "activo_corriente",
    16: "activo_corriente",
    17: "activo_corriente",
    18: "activo_corriente",
    20: "activo_corriente",
    21: "activo_corriente",
    22: "activo_corriente",
    23: "activo_corriente",
    24: "activo_corriente",
    25: "activo_corriente",
    26: "activo_corriente",
    27: "activo_corriente",
    28: "activo_corriente",
    29: "activo_corriente",

    # ACTIVO NO CORRIENTE
    30: "activo_no_corriente",
    31: "activo_no_corriente",
    32: "activo_no_corriente",
    33: "activo_no_corriente",
    34: "activo_no_corriente",
    35: "activo_no_corriente",
    36: "activo_no_corriente",
    37: "activo_no_corriente",
    38: "activo_no_corriente",
    39: "activo_no_corriente",   # Depreciación acumulada (cuenta reguladora)

    # PASIVO CORRIENTE
    40: "pasivo_corriente",
    41: "pasivo_corriente",
    42: "pasivo_corriente",
    43: "pasivo_corriente",
    44: "pasivo_corriente",
    45: "pasivo_corriente",
    46: "pasivo_corriente",
    47: "pasivo_corriente",
    48: "pasivo_corriente",

    # PASIVO NO CORRIENTE
    49: "pasivo_no_corriente",

    # PATRIMONIO
    50: "patrimonio",
    51: "patrimonio",
    52: "patrimonio",
    56: "patrimonio",
    57: "patrimonio",
    58: "patrimonio",
    59: "patrimonio",
}


def _clasificar_cuenta(cod_cuenta: int) -> str:
    """Retorna la sección ESF de una cuenta de 2 dígitos."""
    return _CLASIFICACION.get(cod_cuenta, "otros")


def obtener_estado_situacion_financiera(fecha_corte: str = None) -> dict:
    """
    Genera el Estado de Situación Financiera usando solo cuentas de 2 dígitos.

    ACTIVO = PASIVO + PATRIMONIO + Resultado del Ejercicio
    """
    from datetime import date

    if fecha_corte is None:
        fecha_corte = str(date.today())

    # Solo saldos de cuentas de 2 dígitos (10–99)
    saldos = obtener_saldos_por_cuenta()

    resultado_ejercicio = _calcular_resultado_ejercicio()

    secciones = {
        "activo_corriente":    [],
        "activo_no_corriente": [],
        "pasivo_corriente":    [],
        "pasivo_no_corriente": [],
        "patrimonio":          [],
    }

    for cod, info in sorted(saldos.items()):
        seccion = _clasificar_cuenta(cod)
        if seccion not in secciones:
            continue  # Ignora cuentas de gasto/ingreso (60-99)

        debe  = info["debe"]
        haber = info["haber"]

        # Cuenta 39 (Depreciación) es reguladora → saldo acreedor reduce activo
        if cod == 39:
            valor = round(haber - debe, 2)
            if valor == 0:
                continue
            secciones["activo_no_corriente"].append({
                "cod_cuenta":    cod,
                "nombre_cuenta": info["nombre"],
                "debe":          round(debe, 2),
                "haber":         round(haber, 2),
                "saldo":         round(debe - haber, 2),
                "valor":         -valor   # resta al activo no corriente
            })
            continue

        saldo = round(debe - haber, 2)
        if saldo == 0 and debe == 0:
            continue

        item = {
            "cod_cuenta":    cod,
            "nombre_cuenta": info["nombre"],
            "debe":          round(debe,  2),
            "haber":         round(haber, 2),
            "saldo":         saldo
        }

        if seccion.startswith("activo"):
            item["valor"] = saldo               # activo: saldo deudor es positivo
        else:
            item["valor"] = round(haber - debe, 2)  # pasivo/patrimonio: saldo acreedor

        secciones[seccion].append(item)

    # ── Totales ───────────────────────────────────────────────
    tot_ac  = round(sum(i["valor"] for i in secciones["activo_corriente"]),    2)
    tot_anc = round(sum(i["valor"] for i in secciones["activo_no_corriente"]), 2)
    tot_pc  = round(sum(i["valor"] for i in secciones["pasivo_corriente"]),    2)
    tot_pnc = round(sum(i["valor"] for i in secciones["pasivo_no_corriente"]), 2)
    tot_pat = round(sum(i["valor"] for i in secciones["patrimonio"]),          2)

    total_activo          = round(tot_ac + tot_anc, 2)
    total_pasivo          = round(tot_pc + tot_pnc, 2)
    total_pasivo_patrimonio = round(total_pasivo + tot_pat + resultado_ejercicio, 2)

    cuadrado   = total_activo == total_pasivo_patrimonio
    diferencia = round(total_activo - total_pasivo_patrimonio, 2)

    return {
        "fecha_corte": fecha_corte,
        "activo": {
            "corriente":          secciones["activo_corriente"],
            "no_corriente":       secciones["activo_no_corriente"],
            "total_corriente":    tot_ac,
            "total_no_corriente": tot_anc,
            "total_activo":       total_activo
        },
        "pasivo": {
            "corriente":          secciones["pasivo_corriente"],
            "no_corriente":       secciones["pasivo_no_corriente"],
            "total_corriente":    tot_pc,
            "total_no_corriente": tot_pnc,
            "total_pasivo":       total_pasivo
        },
        "patrimonio": {
            "detalle":             secciones["patrimonio"],
            "total_patrimonio":    tot_pat,
            "resultado_ejercicio": resultado_ejercicio
        },
        "total_pasivo_patrimonio": total_pasivo_patrimonio,
        "cuadrado":   cuadrado,
        "diferencia": diferencia
    }


def _calcular_resultado_ejercicio() -> float:
    """
    Resultado del ejercicio = Ingresos (70-79) − Gastos (60-69).
    Solo usa cuentas de 2 dígitos.
    """
    conexion = obtener_conexion()
    if not conexion:
        return 0.0

    try:
        cursor = conexion.cursor()

        # Ingresos: cuentas 70–79 → saldo esperado HABER
        cursor.execute("""
            SELECT ISNULL(SUM(SALDO_HABER_CUENTA - SALDO_DEBE_CUENTA), 0)
            FROM CUENTA
            WHERE COD_CUENTA BETWEEN 70 AND 79
        """)
        ingresos = float(cursor.fetchone()[0] or 0)

        # Gastos: cuentas 60–69 → saldo esperado DEBE
        cursor.execute("""
            SELECT ISNULL(SUM(SALDO_DEBE_CUENTA - SALDO_HABER_CUENTA), 0)
            FROM CUENTA
            WHERE COD_CUENTA BETWEEN 60 AND 69
        """)
        gastos = float(cursor.fetchone()[0] or 0)

        return round(ingresos - gastos, 2)

    except Exception as e:
        print(f"[ERROR] _calcular_resultado_ejercicio: {e}")
        return 0.0
    finally:
        cerrar_conexion(conexion)