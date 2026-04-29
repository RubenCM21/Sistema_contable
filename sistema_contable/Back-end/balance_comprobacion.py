# ============================================================
# balance_comprobacion.py
# Sistema Contable - Balance de Comprobación
#
# CORRECCIÓN: cada cuenta muestra su saldo neto solo en
# la columna que corresponde a su naturaleza:
#   Cuentas Deudoras  → saldo en columna DEBE,  haber = 0
#   Cuentas Acreedoras→ saldo en columna HABER, debe  = 0
#
# Esto es la presentación estándar del Balance de Comprobación
# de Saldos (no de Sumas).
# ============================================================

from conexion_bd import obtener_conexion, cerrar_conexion, generar_balance_comprobacion
from libro_mayor import obtener_saldos_por_cuenta


def obtener_balance_comprobacion(mes: int = None, anio: int = None) -> dict:
    """
    Genera el Balance de Comprobación de Saldos.

    Cada cuenta aparece UNA sola vez con su saldo neto
    ubicado en la columna correcta:
      - Cuenta deudora  (activos, gastos) → debe = saldo_neto, haber = 0
      - Cuenta acreedora(pasivos, patr, ingresos) → debe = 0, haber = saldo_neto

    Retorna:
    {
      "cod_balance": int,
      "periodo": "MM/YYYY",
      "detalle": [
        { "cod_cuenta", "nombre_cuenta",
          "debe": float,   ← saldo neto si es deudora, 0 si acreedora
          "haber": float   ← 0 si deudora, saldo neto si acreedora
        }, ...
      ],
      "total_debe":  float,
      "total_haber": float,
      "cuadrado": bool,
      "estado": "CUADRADO" | "DESCUADRADO"
    }
    """
    from datetime import date

    if mes  is None: mes  = date.today().month
    if anio is None: anio = date.today().year

    saldos = obtener_saldos_por_cuenta()   # ya filtrado a 2 dígitos

    detalle     = []
    total_debe  = 0.0
    total_haber = 0.0

    for cod, info in sorted(saldos.items()):
        saldo = info["saldo_neto"]

        if saldo == 0:
            continue   # cuenta en cero, no mostrar

        # Colocar el saldo en la columna correcta
        # Si el saldo_neto es negativo (saldo contrario a su naturaleza)
        # lo mostramos igual en la columna opuesta para reflejar la realidad
        if saldo >= 0:
            # saldo en su columna natural
            debe_fila  = saldo if not _es_haber(cod) else 0.0
            haber_fila = saldo if     _es_haber(cod) else 0.0
        else:
            # saldo contrario (p.e. activo con más haber que debe)
            saldo_abs  = abs(saldo)
            debe_fila  = saldo_abs if     _es_haber(cod) else 0.0
            haber_fila = saldo_abs if not _es_haber(cod) else 0.0

        detalle.append({
            "cod_cuenta":    cod,
            "nombre_cuenta": info["nombre"],
            "debe":          round(debe_fila,  2),
            "haber":         round(haber_fila, 2),
        })
        total_debe  += debe_fila
        total_haber += haber_fila

    total_debe  = round(total_debe,  2)
    total_haber = round(total_haber, 2)
    cuadrado    = abs(total_debe - total_haber) < 0.01

    # Persistir en BD
    cod_balance = generar_balance_comprobacion(mes, anio)

    return {
        "cod_balance":  cod_balance,
        "periodo":      f"{mes:02d}/{anio}",
        "detalle":      detalle,
        "total_debe":   total_debe,
        "total_haber":  total_haber,
        "cuadrado":     cuadrado,
        "estado":       "CUADRADO" if cuadrado else "DESCUADRADO",
    }


# ─── Helper local (evita importar libro_mayor dos veces) ─────
_PRIMER_DIGITO_HABER = {4, 5, 7, 8}

def _es_haber(cod_cuenta: int) -> bool:
    return int(str(cod_cuenta)[0]) in _PRIMER_DIGITO_HABER


# ─── Historial y detalle (sin cambios) ───────────────────────

def obtener_historial_balances() -> list:
    conexion = obtener_conexion()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT COD_BALANCE, MES, ANIO,
                   SALDO_DEBE_TOTAL, SALDO_HABER_TOTAL, ESTADO_BALANCE
            FROM BALANCE_COMPROBACION
            ORDER BY ANIO DESC, MES DESC
        """)
        return [
            {
                "cod_balance":  f[0],
                "mes":          f[1],
                "anio":         f[2],
                "total_debe":   float(f[3] or 0),
                "total_haber":  float(f[4] or 0),
                "estado":       f[5],
            }
            for f in cursor.fetchall()
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
            FROM BALANCE_COMPROBACION WHERE COD_BALANCE = ?
        """, (cod_balance,))
        cab = cursor.fetchone()
        if not cab:
            return {"error": "Balance no encontrado"}

        cursor.execute("""
            SELECT BCD.COD_CUENTA, C.NOMBRE_CUENTA,
                   BCD.SALDO_DEBE, BCD.SALDO_HABER
            FROM BALANCE_COMPROBACION_DETALLE BCD
            JOIN CUENTA C ON BCD.COD_CUENTA = C.COD_CUENTA
            WHERE BCD.COD_BALANCE = ?
            ORDER BY BCD.COD_CUENTA
        """, (cod_balance,))
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
                    "haber":         float(d[3] or 0),
                }
                for d in cursor.fetchall()
            ],
        }
    except Exception as e:
        print(f"[ERROR] obtener_detalle_balance: {e}")
        return {}
    finally:
        cerrar_conexion(conexion)