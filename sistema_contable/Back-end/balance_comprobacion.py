# ============================================================
# balance_comprobacion.py
# Sistema Contable - Balance de Comprobación
# Corregido: solo cuentas de 2 dígitos
# ============================================================

from conexion_bd import obtener_conexion, cerrar_conexion, generar_balance_comprobacion
from libro_mayor import obtener_saldos_por_cuenta


def obtener_balance_comprobacion(mes: int = None, anio: int = None) -> dict:
    """
    Genera el Balance de Comprobación usando solo cuentas de 2 dígitos.

    Retorna:
    {
      "cod_balance": int | None,
      "periodo": "MM/YYYY",
      "detalle": [ {"cod_cuenta", "nombre_cuenta", "debe", "haber"}, ... ],
      "total_debe": float,
      "total_haber": float,
      "cuadrado": bool,
      "estado": "CUADRADO" | "DESCUADRADO"
    }
    """
    from datetime import date

    if mes is None:
        mes  = date.today().month
    if anio is None:
        anio = date.today().year

    # Solo saldos de cuentas de 2 dígitos (filtrado en obtener_saldos_por_cuenta)
    saldos = obtener_saldos_por_cuenta()

    detalle     = []
    total_debe  = 0.0
    total_haber = 0.0

    for cod, info in sorted(saldos.items()):
        debe  = info["debe"]
        haber = info["haber"]

        if debe == 0 and haber == 0:
            continue

        detalle.append({
            "cod_cuenta":    cod,
            "nombre_cuenta": info["nombre"],
            "debe":          round(debe,  2),
            "haber":         round(haber, 2)
        })
        total_debe  += debe
        total_haber += haber

    total_debe  = round(total_debe,  2)
    total_haber = round(total_haber, 2)
    cuadrado    = total_debe == total_haber

    cod_balance = generar_balance_comprobacion(mes, anio)

    return {
        "cod_balance":  cod_balance,
        "periodo":      f"{mes:02d}/{anio}",
        "detalle":      detalle,
        "total_debe":   total_debe,
        "total_haber":  total_haber,
        "cuadrado":     cuadrado,
        "estado":       "CUADRADO" if cuadrado else "DESCUADRADO"
    }


def obtener_historial_balances() -> list:
    conexion = obtener_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                COD_BALANCE, MES, ANIO,
                SALDO_DEBE_TOTAL, SALDO_HABER_TOTAL, ESTADO_BALANCE
            FROM BALANCE_COMPROBACION
            ORDER BY ANIO DESC, MES DESC
        """)
        filas = cursor.fetchall()

        return [
            {
                "cod_balance":  f[0],
                "mes":          f[1],
                "anio":         f[2],
                "total_debe":   float(f[3] or 0),
                "total_haber":  float(f[4] or 0),
                "estado":       f[5]
            }
            for f in filas
        ]
    except Exception as e:
        print(f"[ERROR] obtener_historial_balances: {e}")
        return []
    finally:
        cerrar_conexion(conexion)


def obtener_detalle_balance(cod_balance: int) -> dict:
    conexion = obtener_conexion()
    if not conexion:
        return {}

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT MES, ANIO, SALDO_DEBE_TOTAL, SALDO_HABER_TOTAL, ESTADO_BALANCE
            FROM BALANCE_COMPROBACION
            WHERE COD_BALANCE = ?
        """, (cod_balance,))
        cab = cursor.fetchone()
        if not cab:
            return {"error": "Balance no encontrado"}

        cursor.execute("""
            SELECT BCD.COD_CUENTA, C.NOMBRE_CUENTA, BCD.SALDO_DEBE, BCD.SALDO_HABER
            FROM BALANCE_COMPROBACION_DETALLE BCD
            JOIN CUENTA C ON BCD.COD_CUENTA = C.COD_CUENTA
            WHERE BCD.COD_BALANCE = ?
            ORDER BY BCD.COD_CUENTA
        """, (cod_balance,))
        det = cursor.fetchall()

        return {
            "cod_balance": cod_balance,
            "periodo":     f"{cab[0]:02d}/{cab[1]}",
            "total_debe":  float(cab[2] or 0),
            "total_haber": float(cab[3] or 0),
            "estado":      cab[4],
            "detalle": [
                {
                    "cod_cuenta":    d[0],
                    "nombre_cuenta": d[1],
                    "debe":          float(d[2] or 0),
                    "haber":         float(d[3] or 0)
                }
                for d in det
            ]
        }
    except Exception as e:
        print(f"[ERROR] obtener_detalle_balance: {e}")
        return {}
    finally:
        cerrar_conexion(conexion)