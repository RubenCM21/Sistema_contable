# ============================================================
# conexion_bd.py
# Sistema Contable - Conexión y funciones base
# SQL Server con Windows Authentication
# ============================================================

import pyodbc
from datetime import date, datetime


# ------------------------------------------------------------
# CONFIGURACIÓN DE CONEXIÓN
# ------------------------------------------------------------

SERVIDOR   = r'localhost'   # nombre de tu servidor (lo viste en SSMS)
BASE_DATOS = 'SistemaContable'
DRIVER     = '{ODBC Driver 17 for SQL Server}'

# Con Windows Authentication no necesitas usuario ni contraseña
CADENA_CONEXION = (
    f"DRIVER={DRIVER};"
    f"SERVER={SERVIDOR};"
    f"DATABASE={BASE_DATOS};"
    f"UID=sa;"
    f"PWD=123456789;"
)


# ------------------------------------------------------------
# FUNCIONES DE CONEXIÓN
# ------------------------------------------------------------

def obtener_conexion():
    """
    Abre y retorna una conexión activa a SQL Server.
    Retorna None si falla, imprimiendo el error.
    """
    try:
        conexion = pyodbc.connect(CADENA_CONEXION)
        return conexion
    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        return None


def cerrar_conexion(conexion):
    """Cierra la conexión si está activa."""
    if conexion:
        conexion.close()


def probar_conexion():
    """
    Prueba rápida: intenta conectar e imprime el resultado.
    Útil para verificar que todo está bien configurado.
    """
    print("Probando conexión a SQL Server...")
    conexion = obtener_conexion()
    if conexion:
        print(f"[OK] Conexión exitosa → {SERVIDOR} / {BASE_DATOS}")
        cerrar_conexion(conexion)
    else:
        print("[FALLO] Revisa el nombre del servidor o el driver instalado.")


# ------------------------------------------------------------
# FUNCIONES DE CUENTA
# ------------------------------------------------------------

def insertar_cuenta(cod_cuenta, nombre_cuenta, grupo_cuenta, tipo_cuenta):
    """
    Inserta una cuenta en el plan de cuentas.
    Si la cuenta ya existe, no la duplica.

    Parámetros:
        cod_cuenta    : int   → número de cuenta (ej. 10, 70)
        nombre_cuenta : str   → nombre (ej. 'Caja')
        grupo_cuenta  : str   → 'ACTIVO', 'PASIVO' o 'CAPITAL'
        tipo_cuenta   : str   → tipo específico (ej. 'CAJA', 'INVENTARIOS')
    """
    conexion = obtener_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()

        # Verificar si la cuenta ya existe
        cursor.execute(
            "SELECT COUNT(*) FROM CUENTA WHERE COD_CUENTA = ?",
            (cod_cuenta,)
        )
        if cursor.fetchone()[0] > 0:
            print(f"[INFO] Cuenta {cod_cuenta} ya existe, se omite.")
            return True

        cursor.execute("""
            INSERT INTO CUENTA (COD_CUENTA, NOMBRE_CUENTA, GRUPO_CUENTA, TIPO_CUENTA)
            VALUES (?, ?, ?, ?)
        """, (cod_cuenta, nombre_cuenta, grupo_cuenta, tipo_cuenta))

        conexion.commit()
        print(f"[OK] Cuenta {cod_cuenta} - {nombre_cuenta} insertada.")
        return True

    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo insertar la cuenta {cod_cuenta}: {e}")
        conexion.rollback()
        return False
    finally:
        cerrar_conexion(conexion)


def obtener_cuenta(cod_cuenta):
    """
    Retorna los datos de una cuenta por su código.
    Retorna None si no existe.
    """
    conexion = obtener_conexion()
    if not conexion:
        return None

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT * FROM CUENTA WHERE COD_CUENTA = ?",
            (cod_cuenta,)
        )
        return cursor.fetchone()
    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo obtener la cuenta {cod_cuenta}: {e}")
        return None
    finally:
        cerrar_conexion(conexion)


def actualizar_saldo_cuenta(cod_cuenta, monto, tipo_movimiento):
    """
    Actualiza el saldo DEBE o HABER de una cuenta.

    Parámetros:
        cod_cuenta       : int  → código de cuenta
        monto            : float
        tipo_movimiento  : str  → 'D' (Debe) o 'H' (Haber)
    """
    conexion = obtener_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()

        if tipo_movimiento == 'D':
            cursor.execute("""
                UPDATE CUENTA
                SET SALDO_DEBE_CUENTA = SALDO_DEBE_CUENTA + ?
                WHERE COD_CUENTA = ?
            """, (monto, cod_cuenta))
        elif tipo_movimiento == 'H':
            cursor.execute("""
                UPDATE CUENTA
                SET SALDO_HABER_CUENTA = SALDO_HABER_CUENTA + ?
                WHERE COD_CUENTA = ?
            """, (monto, cod_cuenta))
        else:
            print(f"[ERROR] Tipo de movimiento inválido: '{tipo_movimiento}'. Use 'D' o 'H'.")
            return False

        conexion.commit()
        return True

    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo actualizar saldo de cuenta {cod_cuenta}: {e}")
        conexion.rollback()
        return False
    finally:
        cerrar_conexion(conexion)


# ------------------------------------------------------------
# FUNCIONES DE ASIENTO
# ------------------------------------------------------------

def insertar_asiento(fecha, glosa, total_cuentas, saldo_debe, saldo_haber):
    """
    Inserta un asiento contable (cabecera del diario).
    Retorna el COD_ASIENTO generado, o None si falla.

    Parámetros:
        fecha          : date   → fecha del asiento
        glosa          : str    → descripción de la transacción
        total_cuentas  : int    → número de cuentas afectadas
        saldo_debe     : float  → total del lado Debe
        saldo_haber    : float  → total del lado Haber
    """
    conexion = obtener_conexion()
    if not conexion:
        return None

    try:
        cursor = conexion.cursor()

        # Verificar que el asiento cuadre (Debe == Haber)
        if round(saldo_debe, 2) != round(saldo_haber, 2):
            estado = 'DESCUADRADO'
            print(f"[ADVERTENCIA] Asiento descuadrado: Debe={saldo_debe} / Haber={saldo_haber}")
        else:
            estado = 'CUADRADO'

        cursor.execute("""
            INSERT INTO ASIENTO (
                FECHA_REGISTRO_ASIENTO,
                GLOSA_ASIENTO,
                TOTAL_CUENTAS_AFECTADAS,
                SALDO_DEBE_ASIENTO,
                SALDO_HABER_ASIENTO,
                ESTADO_ASIENTO
            )
            OUTPUT INSERTED.COD_ASIENTO
            VALUES (?, ?, ?, ?, ?, ?)
        """, (fecha, glosa, total_cuentas, saldo_debe, saldo_haber, estado))

        cod_asiento = cursor.fetchone()[0]
        conexion.commit()
        print(f"[OK] Asiento #{cod_asiento} registrado → {glosa}")
        return cod_asiento

    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo insertar el asiento: {e}")
        conexion.rollback()
        return None
    finally:
        cerrar_conexion(conexion)


def obtener_asientos():
    """Retorna todos los asientos registrados, ordenados por fecha."""
    conexion = obtener_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT COD_ASIENTO, FECHA_REGISTRO_ASIENTO, GLOSA_ASIENTO,
                   SALDO_DEBE_ASIENTO, SALDO_HABER_ASIENTO, ESTADO_ASIENTO
            FROM ASIENTO
            ORDER BY FECHA_REGISTRO_ASIENTO
        """)
        return cursor.fetchall()
    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo obtener los asientos: {e}")
        return []
    finally:
        cerrar_conexion(conexion)


# ------------------------------------------------------------
# FUNCIONES DE PARTIDA
# ------------------------------------------------------------

def insertar_partida(cod_asiento, cod_cuenta, tipo_movimiento, monto):
    """
    Inserta una línea de partida dentro de un asiento.
    También actualiza automáticamente el saldo de la cuenta afectada.

    Parámetros:
        cod_asiento     : int   → asiento al que pertenece
        cod_cuenta      : int   → cuenta afectada
        tipo_movimiento : str   → 'D' (Debe) o 'H' (Haber)
        monto           : float → importe de la partida
    """
    conexion = obtener_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO PARTIDA (COD_ASIENTO, COD_CUENTA, TIPO_MOVIMIENTO, MONTO_PARTIDA)
            VALUES (?, ?, ?, ?)
        """, (cod_asiento, cod_cuenta, tipo_movimiento, monto))

        conexion.commit()

        # Actualizar saldo de la cuenta afectada
        actualizar_saldo_cuenta(cod_cuenta, monto, tipo_movimiento)

        print(f"[OK] Partida registrada → Asiento #{cod_asiento} | "
              f"Cuenta {cod_cuenta} | {tipo_movimiento} | S/ {monto:.2f}")
        return True

    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo insertar la partida: {e}")
        conexion.rollback()
        return False
    finally:
        cerrar_conexion(conexion)


# ------------------------------------------------------------
# FUNCIONES DE TRANSACCIÓN
# ------------------------------------------------------------

def insertar_transaccion(cod_asiento, tipo, subtipo, fecha, monto, cod_metodo_pago):
    """
    Inserta la clasificación de una transacción contable.

    Parámetros:
        cod_asiento      : int   → asiento relacionado
        tipo             : str   → 'APORTE', 'COMPRA', 'INGRESO', 'DEVOLUCION',
                                   'PERDIDA', 'PAGO', 'DEPRECIACION'
        subtipo          : str   → 'MERCADERIA', 'SERVICIO', 'CAPITAL', 'VENTA', etc.
        fecha            : date  → fecha de la transacción
        monto            : float → monto total
        cod_metodo_pago  : int   → 1 = CONTADO, 2 = CREDITO
    """
    conexion = obtener_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO TRANSACCION (
                COD_ASIENTO, COD_METODO_PAGO,
                TIPO_TRANSACCION, SUB_TIPO_TRANSACCION,
                FECHA_REGISTRO_TRANSACCION, MONTO_TRANSACCION
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cod_asiento, cod_metodo_pago, tipo, subtipo, fecha, monto))

        conexion.commit()
        print(f"[OK] Transacción registrada → {tipo} / {subtipo} | S/ {monto:.2f}")
        return True

    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo insertar la transacción: {e}")
        conexion.rollback()
        return False
    finally:
        cerrar_conexion(conexion)


# ------------------------------------------------------------
# FUNCIONES DEL MAYOR
# ------------------------------------------------------------

def obtener_mayor_por_cuenta(cod_cuenta):
    """
    Retorna todos los movimientos de una cuenta desde la vista MAYOR.
    Útil para imprimir el libro mayor de una cuenta específica.
    """
    conexion = obtener_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                FECHA_REGISTRO_ASIENTO,
                GLOSA_ASIENTO,
                DEBE,
                HABER
            FROM MAYOR
            WHERE COD_CUENTA = ?
            ORDER BY FECHA_REGISTRO_ASIENTO
        """, (cod_cuenta,))
        return cursor.fetchall()
    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo obtener el mayor de cuenta {cod_cuenta}: {e}")
        return []
    finally:
        cerrar_conexion(conexion)


def obtener_mayor_completo():
    """Retorna todos los movimientos de todas las cuentas desde la vista MAYOR."""
    conexion = obtener_conexion()
    if not conexion:
        return []

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT COD_CUENTA, NOMBRE_CUENTA, FECHA_REGISTRO_ASIENTO,
                   GLOSA_ASIENTO, DEBE, HABER
            FROM MAYOR
            ORDER BY COD_CUENTA, FECHA_REGISTRO_ASIENTO
        """)
        return cursor.fetchall()
    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo obtener el mayor completo: {e}")
        return []
    finally:
        cerrar_conexion(conexion)


# ------------------------------------------------------------
# FUNCIONES DEL BALANCE DE COMPROBACIÓN
# ------------------------------------------------------------

def generar_balance_comprobacion(mes, anio):
    """
    Genera el balance de comprobación para un mes y año dado.
    Lee los saldos actuales de todas las cuentas y los consolida.
    Retorna el COD_BALANCE generado, o None si falla.

    Parámetros:
        mes  : int → mes del corte (ej. 9 para septiembre)
        anio : int → año del corte (ej. 2024)
    """
    conexion = obtener_conexion()
    if not conexion:
        return None

    try:
        cursor = conexion.cursor()

        # Calcular totales generales
        cursor.execute("""
            SELECT
                SUM(SALDO_DEBE_CUENTA)  AS TOTAL_DEBE,
                SUM(SALDO_HABER_CUENTA) AS TOTAL_HABER
            FROM CUENTA
            WHERE ESTADO_CUENTA = 1
        """)
        fila = cursor.fetchone()
        total_debe  = fila[0] or 0
        total_haber = fila[1] or 0
        estado = 'CUADRADO' if round(total_debe, 2) == round(total_haber, 2) else 'DESCUADRADO'

        # Insertar cabecera del balance
        cursor.execute("""
            INSERT INTO BALANCE_COMPROBACION (MES, ANIO, SALDO_DEBE_TOTAL, SALDO_HABER_TOTAL, ESTADO_BALANCE)
            OUTPUT INSERTED.COD_BALANCE
            VALUES (?, ?, ?, ?, ?)
        """, (mes, anio, total_debe, total_haber, estado))

        cod_balance = cursor.fetchone()[0]

        # Insertar detalle por cuenta
        cursor.execute("SELECT COD_CUENTA, SALDO_DEBE_CUENTA, SALDO_HABER_CUENTA FROM CUENTA WHERE ESTADO_CUENTA = 1")
        cuentas = cursor.fetchall()

        for cuenta in cuentas:
            cursor.execute("""
                INSERT INTO BALANCE_COMPROBACION_DETALLE (COD_BALANCE, COD_CUENTA, SALDO_DEBE, SALDO_HABER)
                VALUES (?, ?, ?, ?)
            """, (cod_balance, cuenta[0], cuenta[1], cuenta[2]))

        conexion.commit()
        print(f"[OK] Balance de comprobación generado → {mes}/{anio} | Estado: {estado}")
        print(f"     Total Debe: S/ {total_debe:.2f} | Total Haber: S/ {total_haber:.2f}")
        return cod_balance

    except pyodbc.Error as e:
        print(f"[ERROR] No se pudo generar el balance de comprobación: {e}")
        conexion.rollback()
        return None
    finally:
        cerrar_conexion(conexion)


# ------------------------------------------------------------
# PUNTO DE ENTRADA — prueba al ejecutar directamente
# ------------------------------------------------------------

if __name__ == "__main__":
    probar_conexion()