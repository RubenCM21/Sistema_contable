from dotenv import load_dotenv
load_dotenv()

import os
import json
import re
import google.generativeai as genai
from plan_cuentas import PLAN_CUENTAS, normalizar_codigo

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
cliente_ai = genai.GenerativeModel("gemini-2.5-flash")

# ============================================================
# CUENTAS PROHIBIDAS — nunca deben aparecer en asientos simples
# Son cuentas intermedias/analíticas que la IA tiende a duplicar
# ============================================================
CUENTAS_PROHIBIDAS = {
    60,  # Compras — usar 20 directamente
    61,  # Variación de Existencias — no se usa en asientos simples
    79,  # Cargas Imputables — solo en sistemas de costeo completo
    78,  # Cargas Cubiertas por Provisiones — idem
}

# ============================================================
# TIPOS DE ASIENTO PERMITIDOS — máximo 2 cuentas por asiento
# Clave: frozenset de los códigos involucrados
# Valor: descripción (solo para documentación)
# ============================================================
PATRONES_VALIDOS = [
    # Activo / Pasivo / Patrimonio
    {10, 50},  # Aporte de capital
    {10, 45},  # Préstamo recibido
    {45, 10},  # Pago préstamo
    {10, 12},  # Cobro cliente
    {42, 10},  # Pago proveedor
    {10, 40},  # Pago tributos
    {10, 41},  # Pago remuneraciones
    # Compras
    {20, 10},  # Compra contado
    {20, 42},  # Compra crédito
    {24, 10},  # Compra mat. prima contado
    {24, 42},  # Compra mat. prima crédito
    {21, 10},  # Compra prod. terminado
    # Ventas
    {10, 70},  # Venta contado
    {12, 70},  # Venta crédito
    # Costo de ventas
    {69, 20},  # Costo de venta mercadería
    {69, 21},  # Costo de venta prod. terminado
    {69, 24},  # Costo de venta mat. prima
    # Gastos
    {62, 10},  # Gastos personal contado
    {62, 41},  # Gastos personal crédito
    {63, 10},  # Gastos servicios contado
    {63, 42},  # Gastos servicios crédito
    {64, 10},  # Gastos tributos
    {64, 40},  # Tributos por pagar
    {65, 10},  # Otros gastos
    {67, 10},  # Gastos financieros
    {67, 45},  # Intereses de préstamo
    {68, 39},  # Depreciación
    # IGV
    {20, 40, 10},   # Compra con IGV contado
    {20, 40, 42},   # Compra con IGV crédito
    {12, 70, 40},   # Venta crédito con IGV
    {10, 70, 40},   # Venta contado con IGV
    # Activos fijos
    {33, 10},  # Compra activo fijo contado
    {33, 42},  # Compra activo fijo crédito
    {33, 45},  # Compra activo fijo financiado
]

SYSTEM_PROMPT = """Eres un contador peruano experto en PCGE. Genera asientos contables SIMPLES y EXACTOS.

REGLA ABSOLUTA: UN HECHO ECONÓMICO = UN ASIENTO (máximo 2-3 partidas)

ASIENTOS CORRECTOS:
- Aporte capital:      10 D / 50 H
- Compra contado:      20 D / 10 H
- Compra crédito:      20 D / 42 H
- Venta contado:       10 D / 70 H  +  asiento separado: 69 D / 20 H
- Venta crédito:       12 D / 70 H  +  asiento separado: 69 D / 20 H
- Pago gasto:          63 D / 10 H
- Pago sueldos:        62 D / 10 H
- Depreciación:        68 D / 39 H
- Préstamo recibido:   10 D / 45 H
- Pago préstamo:       45 D / 10 H
- Cobro cliente:       10 D / 12 H
- Pago proveedor:      42 D / 10 H

PROHIBIDO ABSOLUTAMENTE:
- NO usar cuenta 60 (Compras) ni 61 (Variación Existencias)
- NO usar cuenta 79 ni 78
- NO generar asiento de "destino al almacén" por separado
- NO generar más de 2 asientos por operación
- NO usar códigos de 3+ dígitos

CUENTAS DISPONIBLES (solo 2 dígitos):
10 Efectivo, 12 CxC Terceros, 20 Mercaderías, 21 Prod.Terminados,
24 Mat.Primas, 33 IME, 39 Deprec.Acum., 40 Tributos, 41 Remuner.,
42 CxP Terceros, 45 Oblig.Financieras, 50 Capital, 59 Result.Acum.,
62 Gtos.Personal, 63 Gtos.Servicios, 64 Gtos.Tributos, 65 Otros Gastos,
67 Gtos.Financieros, 68 Valuación/Deprec., 69 Costo Ventas,
70 Ventas, 75 Otros Ingresos, 77 Ingresos Financieros

RESPONDE SOLO JSON sin markdown:
{
  "asientos": [
    {
      "fecha": "YYYY-MM-DD",
      "glosa": "descripcion breve",
      "tipo_transaccion": "COMPRA|VENTA|PAGO|COBRO|APORTE|GASTO|OTRO",
      "subtipo": "MERCADERIA|SERVICIO|CAPITAL|PERSONAL|FINANCIERO",
      "metodo_pago": "CONTADO|CREDITO",
      "partidas": [
        {"codigo_cuenta": 10, "nombre_cuenta": "Efectivo y Equivalentes de Efectivo", "tipo_movimiento": "D", "monto": 1000.00},
        {"codigo_cuenta": 50, "nombre_cuenta": "Capital", "tipo_movimiento": "H", "monto": 1000.00}
      ]
    }
  ]
}"""


# ── Filtros de limpieza ───────────────────────────────────────

def _normalizar_partidas(asiento: dict) -> dict:
    """Normaliza códigos a 2 dígitos y actualiza nombres."""
    limpias = []
    for p in asiento.get("partidas", []):
        cod_2  = normalizar_codigo(p.get("codigo_cuenta", 0))
        nombre = PLAN_CUENTAS.get(cod_2, {}).get("nombre", f"Cuenta {cod_2}")
        limpias.append({
            "codigo_cuenta":   cod_2,
            "nombre_cuenta":   nombre,
            "tipo_movimiento": p.get("tipo_movimiento", "D"),
            "monto":           round(float(p.get("monto", 0)), 2)
        })
    asiento["partidas"] = limpias
    return asiento


def _eliminar_cuentas_prohibidas(asiento: dict) -> dict | None:
    """
    Elimina partidas con cuentas prohibidas.
    Si el asiento queda con menos de 2 partidas, retorna None (descartar).
    Si queda descuadrado, intenta corregirlo.
    """
    partidas_limpias = [
        p for p in asiento.get("partidas", [])
        if p["codigo_cuenta"] not in CUENTAS_PROHIBIDAS
    ]

    if len(partidas_limpias) < 2:
        return None

    asiento["partidas"] = partidas_limpias
    return asiento


def _fusionar_cuentas_repetidas(asiento: dict) -> dict:
    """Fusiona partidas con el mismo código y movimiento."""
    fusionadas = {}
    for p in asiento.get("partidas", []):
        clave = (p["codigo_cuenta"], p["tipo_movimiento"])
        if clave in fusionadas:
            fusionadas[clave]["monto"] += p["monto"]
        else:
            fusionadas[clave] = dict(p)
    asiento["partidas"] = list(fusionadas.values())
    return asiento


def _es_asiento_espejo(asiento: dict, otros: list) -> bool:
    """
    Detecta si este asiento es duplicado o espejo de otro ya procesado.
    Un asiento es espejo si sus cuentas son exactamente las mismas
    pero con D y H invertidos.
    """
    cuentas_d = frozenset(
        p["codigo_cuenta"] for p in asiento["partidas"]
        if p["tipo_movimiento"] == "D"
    )
    cuentas_h = frozenset(
        p["codigo_cuenta"] for p in asiento["partidas"]
        if p["tipo_movimiento"] == "H"
    )

    for otro in otros:
        otras_d = frozenset(
            p["codigo_cuenta"] for p in otro["partidas"]
            if p["tipo_movimiento"] == "D"
        )
        otras_h = frozenset(
            p["codigo_cuenta"] for p in otro["partidas"]
            if p["tipo_movimiento"] == "H"
        )
        # Es espejo si D/H están invertidos con los mismos montos
        if cuentas_d == otras_h and cuentas_h == otras_d:
            montos_asiento = sorted(p["monto"] for p in asiento["partidas"])
            montos_otro    = sorted(p["monto"] for p in otro["partidas"])
            if montos_asiento == montos_otro:
                return True
    return False


def _eliminar_duplicados(asientos: list) -> list:
    """Elimina asientos con firma idéntica o que sean espejos."""
    vistos    = []
    resultado = []

    for asiento in asientos:
        # Firma exacta
        firma = tuple(sorted(
            (p["codigo_cuenta"], p["tipo_movimiento"], round(p["monto"], 2))
            for p in asiento.get("partidas", [])
        ))

        if firma in vistos:
            continue

        # Espejo
        if _es_asiento_espejo(asiento, resultado):
            continue

        vistos.append(firma)
        resultado.append(asiento)

    return resultado


def _corregir_cuadre(asiento: dict) -> dict | None:
    """
    Si el asiento está descuadrado por eliminar cuentas prohibidas,
    ajusta el monto de la partida faltante usando la diferencia.
    Si no puede cuadrarlo, descarta el asiento.
    """
    partidas = asiento.get("partidas", [])
    total_d  = sum(p["monto"] for p in partidas if p["tipo_movimiento"] == "D")
    total_h  = sum(p["monto"] for p in partidas if p["tipo_movimiento"] == "H")

    if round(total_d, 2) == round(total_h, 2):
        return asiento  # ya cuadra

    diferencia = round(abs(total_d - total_h), 2)
    if diferencia == 0:
        return asiento

    # Si hay solo 1 partida de un lado, ajustar su monto
    partidas_d = [p for p in partidas if p["tipo_movimiento"] == "D"]
    partidas_h = [p for p in partidas if p["tipo_movimiento"] == "H"]

    if total_d > total_h and len(partidas_h) == 1:
        partidas_h[0]["monto"] = round(total_d, 2)
        return asiento
    elif total_h > total_d and len(partidas_d) == 1:
        partidas_d[0]["monto"] = round(total_h, 2)
        return asiento

    # No se puede cuadrar automáticamente — descartar
    return None


def _limpiar_pipeline(asientos: list) -> list:
    """
    Pipeline completo de limpieza:
    1. Normalizar códigos
    2. Eliminar cuentas prohibidas
    3. Fusionar partidas repetidas
    4. Corregir cuadre si es posible
    5. Eliminar duplicados y espejos
    """
    limpios = []

    for asiento in asientos:
        # Paso 1: normalizar
        asiento = _normalizar_partidas(asiento)

        # Paso 2: eliminar cuentas prohibidas
        asiento = _eliminar_cuentas_prohibidas(asiento)
        if asiento is None:
            continue

        # Paso 3: fusionar repetidas
        asiento = _fusionar_cuentas_repetidas(asiento)

        # Paso 4: corregir cuadre
        asiento = _corregir_cuadre(asiento)
        if asiento is None:
            continue

        # Solo agregar si tiene al menos 2 partidas
        if len(asiento.get("partidas", [])) >= 2:
            limpios.append(asiento)

    # Paso 5: eliminar duplicados y espejos
    limpios = _eliminar_duplicados(limpios)

    return limpios


# ── Función principal ─────────────────────────────────────────

def interpretar_texto(texto: str) -> dict:
    if not texto or not texto.strip():
        return {"error": "El texto recibido está vacío.", "asientos": []}

    try:
        prompt = (
            SYSTEM_PROMPT
            + "\n\nAnaliza el enunciado. Genera SOLO los asientos estrictamente necesarios.\n\n"
            "ENUNCIADO:\n" + texto
        )

        respuesta = cliente_ai.generate_content(prompt)
        contenido = respuesta.text.strip()
        contenido = re.sub(r"```json\s*", "", contenido)
        contenido = re.sub(r"```\s*",     "", contenido)

        resultado = json.loads(contenido)

        if "asientos" not in resultado:
            return {"error": "La IA no retornó el formato esperado.", "asientos": []}

        # Aplicar pipeline de limpieza
        resultado["asientos"] = _limpiar_pipeline(resultado["asientos"])

        # Validar cuadre final
        resultado = _validar_y_corregir(resultado)
        return resultado

    except json.JSONDecodeError as e:
        return {"error": f"Error al parsear JSON: {e}", "asientos": []}
    except Exception as e:
        return {"error": f"Error en interpretador: {e}", "asientos": []}


def _validar_y_corregir(resultado: dict) -> dict:
    asientos_validados = []

    for asiento in resultado.get("asientos", []):
        total_debe  = sum(p["monto"] for p in asiento.get("partidas", []) if p["tipo_movimiento"] == "D")
        total_haber = sum(p["monto"] for p in asiento.get("partidas", []) if p["tipo_movimiento"] == "H")

        asiento["total_debe"]  = round(total_debe,  2)
        asiento["total_haber"] = round(total_haber, 2)
        asiento["cuadrado"]    = round(total_debe, 2) == round(total_haber, 2)

        if not asiento["cuadrado"]:
            asiento["advertencia"] = (
                f"Asiento descuadrado: DEBE={total_debe:.2f} / HABER={total_haber:.2f}"
            )

        asientos_validados.append(asiento)

    resultado["asientos"]       = asientos_validados
    resultado["total_asientos"] = len(asientos_validados)
    return resultado