# ============================================================
# libro_mayor.py
# Sistema Contable - Generación del Libro Mayor
# Corregido: solo cuentas de 2 dígitos
# ============================================================

from conexion_bd import obtener_conexion, cerrar_conexion


def obtener_libro_mayor(cod_cuenta: int = None) -> list:
    """
    Retorna los movimientos del Libro Mayor.
    Si cod_cuenta es None → retorna todas las cuentas.
    cod_cuenta debe ser de 2 dígitos.
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
        saldo_acumulado = {}

        for f in filas:
            cod = f[0]
            if cod not in saldo_acumulado:
                saldo_acumulado[cod] = 0.0

            debe  = float(f[4] or 0)
            haber = float(f[5] or 0)
            saldo_acumulado[cod] += debe - haber

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


def obtener_mayor_agrupado() -> list:
    """
    Retorna el libro mayor agrupado por cuenta (2 dígitos),
    con totales y saldo final.
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
        saldo = round(data["total_debe"] - data["total_haber"], 2)
        data["total_debe"]  = round(data["total_debe"],  2)
        data["total_haber"] = round(data["total_haber"], 2)
        data["saldo_final"] = abs(saldo)
        data["naturaleza"]  = "DEUDOR" if saldo >= 0 else "ACREEDOR"
        resultado.append(data)

    return resultado


def obtener_saldos_por_cuenta() -> dict:
    """
    Retorna { cod_cuenta (2 dig): {"debe", "haber", "saldo", "nombre"} }
    Solo cuentas activas de 2 dígitos (COD_CUENTA < 100).
    """
    conexion = obtener_conexion()
    if not conexion:
        return {}

    try:
        cursor = conexion.cursor()
        # Filtra solo cuentas de 2 dígitos (10 a 99)
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
            saldos[cod] = {
                "nombre": f[1],
                "debe":   debe,
                "haber":  haber,
                "saldo":  round(debe - haber, 2)
            }
        return saldos

    except Exception as e:
        print(f"[ERROR] obtener_saldos_por_cuenta: {e}")
        return {}
    finally:
        cerrar_conexion(conexion)