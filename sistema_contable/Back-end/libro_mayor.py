# ============================================================
# libro_mayor.py
# Sistema Contable - Generación del Libro Mayor
# CORRECCIÓN: saldo acumulado respeta la naturaleza de la cuenta
#   Cuentas Deudoras  (1x,2x,3x,6x) → saldo = Debe - Haber
#   Cuentas Acreedoras(4x,5x,7x,8x) → saldo = Haber - Debe
# ============================================================

from conexion_bd import obtener_conexion, cerrar_conexion

# ─── Cuentas cuyo saldo normal es HABER (acreedoras) ─────────
# Se identifica por el primer dígito del código de 2 dígitos
_PRIMER_DIGITO_HABER = {4, 5, 7, 8}   # Pasivo, Patrimonio, Ingresos, Cierre

def _es_cuenta_haber(cod_cuenta: int) -> bool:
    """True si la cuenta tiene saldo normal HABER."""
    primer = int(str(cod_cuenta)[0])
    return primer in _PRIMER_DIGITO_HABER


# ─── Libro Mayor plano ────────────────────────────────────────

def obtener_libro_mayor(cod_cuenta: int = None) -> list:
    """
    Retorna los movimientos del Libro Mayor con saldo acumulado
    calculado correctamente según la naturaleza de cada cuenta.
    """
    conexion = obtener_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()

        query = """
            SELECT
                M.COD_CUENTA,
                M.NOMBRE_CUENTA,
                M.FECHA_REGISTRO_ASIENTO,
                M.GLOSA_ASIENTO,
                M.DEBE,
                M.HABER
            FROM MAYOR M
        """
        params = []
        if cod_cuenta is not None:
            query += " WHERE M.COD_CUENTA = ?"
            params.append(int(cod_cuenta))
        query += " ORDER BY M.COD_CUENTA, M.FECHA_REGISTRO_ASIENTO"

        cursor.execute(query, params)
        filas = cursor.fetchall()

        resultado       = []
        saldo_acumulado = {}   # { cod: float }

        for f in filas:
            cod   = f[0]
            debe  = float(f[4] or 0)
            haber = float(f[5] or 0)

            if cod not in saldo_acumulado:
                saldo_acumulado[cod] = 0.0

            # Saldo acumulado según naturaleza
            if _es_cuenta_haber(cod):
                saldo_acumulado[cod] += haber - debe   # acreedora
            else:
                saldo_acumulado[cod] += debe  - haber  # deudora

            resultado.append({
                "cod_cuenta":      cod,
                "nombre_cuenta":   f[1],
                "fecha":           str(f[2]),
                "glosa":           f[3],
                "debe":            debe,
                "haber":           haber,
                "saldo_acumulado": round(saldo_acumulado[cod], 2)
            })

        return resultado

    except Exception as e:
        print(f"[ERROR] obtener_libro_mayor: {e}")
        return []
    finally:
        cerrar_conexion(conexion)


# ─── Libro Mayor agrupado por cuenta ─────────────────────────

def obtener_mayor_agrupado() -> list:
    """
    Libro Mayor agrupado por cuenta con totales y saldo final.

    saldo_final → siempre positivo; naturaleza indica si es
    DEUDOR o ACREEDOR.
    """
    movimientos = obtener_libro_mayor()
    if not movimientos:
        return []

    cuentas: dict = {}
    for mov in movimientos:
        cod = mov["cod_cuenta"]
        if cod not in cuentas:
            cuentas[cod] = {
                "cod_cuenta":    cod,
                "nombre_cuenta": mov["nombre_cuenta"],
                "movimientos":   [],
                "total_debe":    0.0,
                "total_haber":   0.0,
            }
        cuentas[cod]["movimientos"].append(mov)
        cuentas[cod]["total_debe"]  += mov["debe"]
        cuentas[cod]["total_haber"] += mov["haber"]

    resultado = []
    for cod, data in sorted(cuentas.items()):
        td = round(data["total_debe"],  2)
        th = round(data["total_haber"], 2)

        # Saldo neto según naturaleza
        if _es_cuenta_haber(cod):
            saldo_neto = round(th - td, 2)   # acreedora: saldo H
        else:
            saldo_neto = round(td - th, 2)   # deudora:   saldo D

        data["total_debe"]  = td
        data["total_haber"] = th
        data["saldo_final"] = abs(saldo_neto)
        data["naturaleza"]  = "ACREEDOR" if _es_cuenta_haber(cod) else "DEUDOR"
        resultado.append(data)

    return resultado


# ─── Saldos por cuenta para balance y estados financieros ────

def obtener_saldos_por_cuenta() -> dict:
    """
    Retorna { cod_cuenta: {"debe", "haber", "saldo_neto", "nombre"} }

    - debe / haber → acumulados brutos (suma de todos los movimientos)
    - saldo_neto   → saldo según naturaleza (positivo = saldo normal,
                     negativo = saldo contrario a su naturaleza)

    Solo cuentas de 2 dígitos (10–99) con al menos un movimiento.
    """
    conexion = obtener_conexion()
    if not conexion:
        return {}

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                COD_CUENTA,
                NOMBRE_CUENTA,
                SALDO_DEBE_CUENTA,
                SALDO_HABER_CUENTA
            FROM CUENTA
            WHERE ESTADO_CUENTA = 1
              AND COD_CUENTA BETWEEN 10 AND 99
            ORDER BY COD_CUENTA
        """)
        filas = cursor.fetchall()

        saldos = {}
        for f in filas:
            cod   = f[0]
            debe  = float(f[2] or 0)
            haber = float(f[3] or 0)

            if debe == 0 and haber == 0:
                continue  # sin movimientos, no incluir

            if _es_cuenta_haber(cod):
                saldo_neto = round(haber - debe, 2)
            else:
                saldo_neto = round(debe  - haber, 2)

            saldos[cod] = {
                "nombre":     f[1],
                "debe":       debe,
                "haber":      haber,
                "saldo_neto": saldo_neto,
            }
        return saldos

    except Exception as e:
        print(f"[ERROR] obtener_saldos_por_cuenta: {e}")
        return {}
    finally:
        cerrar_conexion(conexion)