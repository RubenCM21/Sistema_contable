# ============================================================
# libro_diario.py
# Sistema Contable - Generación del Libro Diario
# Corregido: solo cuentas de 2 dígitos
# ============================================================

from datetime import date
from conexion_bd import (
    obtener_conexion, cerrar_conexion,
    insertar_asiento, insertar_partida, insertar_transaccion
)
from plan_cuentas import normalizar_codigo, PLAN_CUENTAS


def _limpiar_partidas(partidas: list) -> list:
    """
    Garantiza que todos los códigos en las partidas sean de 2 dígitos.
    Si vienen con más dígitos los normaliza.
    """
    limpias = []
    for p in partidas:
        cod_2  = normalizar_codigo(p.get("codigo_cuenta", 0))
        nombre = PLAN_CUENTAS.get(cod_2, {}).get("nombre", f"Cuenta {cod_2}")
        limpias.append({
            "codigo_cuenta":   cod_2,
            "nombre_cuenta":   nombre,
            "tipo_movimiento": p.get("tipo_movimiento", "D"),
            "monto":           round(float(p.get("monto", 0)), 2)
        })
    return limpias


# ── Inserción desde asientos interpretados ───────────────────

def registrar_asientos_desde_interpretacion(asientos: list) -> dict:
    """
    Recibe la lista de asientos ya interpretados y los inserta en BD.
    Normaliza códigos a 2 dígitos antes de insertar.
    """
    registrados = 0
    errores     = 0
    detalle     = []

    for asiento_data in asientos:
        try:
            fecha_str = asiento_data.get("fecha", str(date.today()))
            if isinstance(fecha_str, str):
                from datetime import datetime
                try:
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                except ValueError:
                    fecha = date.today()
            else:
                fecha = fecha_str

            glosa       = asiento_data.get("glosa", "Sin descripción")
            # Normalizar partidas a 2 dígitos
            partidas    = _limpiar_partidas(asiento_data.get("partidas", []))
            total_debe  = sum(p["monto"] for p in partidas if p["tipo_movimiento"] == "D")
            total_haber = sum(p["monto"] for p in partidas if p["tipo_movimiento"] == "H")
            tipo_trans  = asiento_data.get("tipo_transaccion", "OTRO")
            subtipo     = asiento_data.get("subtipo", "GENERAL")
            metodo      = asiento_data.get("metodo_pago", "CONTADO")
            cod_metodo  = 1 if metodo == "CONTADO" else 2

            # 1. Insertar asiento (cabecera)
            cod_asiento = insertar_asiento(
                fecha         = fecha,
                glosa         = glosa,
                total_cuentas = len(partidas),
                saldo_debe    = round(total_debe, 2),
                saldo_haber   = round(total_haber, 2)
            )

            if not cod_asiento:
                errores += 1
                detalle.append({"glosa": glosa, "estado": "ERROR",
                                "msg": "No se pudo insertar el asiento"})
                continue

            # 2. Insertar cada partida con código de 2 dígitos
            for p in partidas:
                insertar_partida(
                    cod_asiento     = cod_asiento,
                    cod_cuenta      = p["codigo_cuenta"],   # ya es 2 dígitos
                    tipo_movimiento = p["tipo_movimiento"],
                    monto           = p["monto"]
                )

            # 3. Insertar transacción
            insertar_transaccion(
                cod_asiento     = cod_asiento,
                tipo            = tipo_trans,
                subtipo         = subtipo,
                fecha           = fecha,
                monto           = round(total_debe, 2),
                cod_metodo_pago = cod_metodo
            )

            registrados += 1
            detalle.append({
                "cod_asiento": cod_asiento,
                "glosa":       glosa,
                "fecha":       str(fecha),
                "estado":      "OK"
            })

        except Exception as e:
            errores += 1
            detalle.append({
                "glosa":  asiento_data.get("glosa", "?"),
                "estado": "ERROR",
                "msg":    str(e)
            })

    return {
        "registrados": registrados,
        "errores":     errores,
        "detalle":     detalle
    }


# ── Consulta del Libro Diario ─────────────────────────────────

def obtener_libro_diario(fecha_inicio: str = None, fecha_fin: str = None) -> list:
    """
    Retorna todas las filas del Libro Diario.
    Los códigos de cuenta almacenados son de 2 dígitos.
    """
    conexion = obtener_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()

        query = """
            SELECT
                A.COD_ASIENTO,
                A.FECHA_REGISTRO_ASIENTO,
                A.GLOSA_ASIENTO,
                P.COD_CUENTA,
                C.NOMBRE_CUENTA,
                P.TIPO_MOVIMIENTO,
                CASE WHEN P.TIPO_MOVIMIENTO = 'D' THEN P.MONTO_PARTIDA ELSE 0 END AS DEBE,
                CASE WHEN P.TIPO_MOVIMIENTO = 'H' THEN P.MONTO_PARTIDA ELSE 0 END AS HABER,
                A.ESTADO_ASIENTO
            FROM ASIENTO A
            JOIN PARTIDA P ON A.COD_ASIENTO = P.COD_ASIENTO
            JOIN CUENTA  C ON P.COD_CUENTA  = C.COD_CUENTA
        """

        params      = []
        condiciones = []

        if fecha_inicio:
            condiciones.append("A.FECHA_REGISTRO_ASIENTO >= ?")
            params.append(fecha_inicio)
        if fecha_fin:
            condiciones.append("A.FECHA_REGISTRO_ASIENTO <= ?")
            params.append(fecha_fin)

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

        query += " ORDER BY A.FECHA_REGISTRO_ASIENTO, A.COD_ASIENTO, P.TIPO_MOVIMIENTO DESC"

        cursor.execute(query, params)
        filas = cursor.fetchall()

        return [
            {
                "cod_asiento":     f[0],
                "fecha":           str(f[1]),
                "glosa":           f[2],
                "cod_cuenta":      f[3],
                "nombre_cuenta":   f[4],
                "tipo_movimiento": f[5],
                "debe":            float(f[6]),
                "haber":           float(f[7]),
                "estado":          f[8]
            }
            for f in filas
        ]

    except Exception as e:
        print(f"[ERROR] obtener_libro_diario: {e}")
        return []
    finally:
        cerrar_conexion(conexion)


def obtener_resumen_diario() -> dict:
    """Retorna el total general de DEBE y HABER del libro diario."""
    conexion = obtener_conexion()
    if not conexion:
        return {}

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                SUM(CASE WHEN P.TIPO_MOVIMIENTO = 'D' THEN P.MONTO_PARTIDA ELSE 0 END),
                SUM(CASE WHEN P.TIPO_MOVIMIENTO = 'H' THEN P.MONTO_PARTIDA ELSE 0 END)
            FROM PARTIDA P
        """)
        fila = cursor.fetchone()
        td   = round(float(fila[0] or 0), 2)
        th   = round(float(fila[1] or 0), 2)
        return {
            "total_debe":  td,
            "total_haber": th,
            "cuadrado":    td == th
        }
    except Exception as e:
        print(f"[ERROR] obtener_resumen_diario: {e}")
        return {}
    finally:
        cerrar_conexion(conexion)