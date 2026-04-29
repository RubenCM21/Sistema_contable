# ============================================================
# plan_cuentas.py
# Sistema Contable - Plan de Cuentas PCGE Peru
# SOLO CUENTAS DE 2 DÍGITOS (según catálogo permitido)
# ============================================================

PLAN_CUENTAS = {
    # ── ACTIVO CORRIENTE ─────────────────────────────────────
    10: {"nombre": "Efectivo y Equivalentes de Efectivo",                    "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    11: {"nombre": "Inversiones Financieras",                                "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    12: {"nombre": "Cuentas por Cobrar Comerciales - Terceros",              "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    13: {"nombre": "Cuentas por Cobrar Comerciales - Relacionadas",          "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    14: {"nombre": "Cuentas por Cobrar al Personal, Accionistas y Gerentes", "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    16: {"nombre": "Cuentas por Cobrar Diversas - Terceros",                 "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    17: {"nombre": "Cuentas por Cobrar Diversas - Relacionadas",             "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    18: {"nombre": "Servicios y Otros Contratados por Anticipado",           "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},

    # ── EXISTENCIAS ──────────────────────────────────────────
    20: {"nombre": "Mercaderías",                                            "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    21: {"nombre": "Productos Terminados",                                   "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    22: {"nombre": "Subproductos, Desechos y Desperdicios",                  "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    23: {"nombre": "Productos en Proceso",                                   "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    24: {"nombre": "Materias Primas",                                        "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    25: {"nombre": "Materiales Auxiliares, Suministros y Repuestos",         "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    26: {"nombre": "Envases y Embalajes",                                    "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    27: {"nombre": "Activos No Corrientes Mantenidos para la Venta",         "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    28: {"nombre": "Existencias por Recibir",                                "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},
    29: {"nombre": "Desvalorización de Existencias",                         "grupo": "ACTIVO", "tipo": "ACTIVO CORRIENTE"},

    # ── ACTIVO NO CORRIENTE ──────────────────────────────────
    30: {"nombre": "Inversiones Mobiliarias",                                "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    31: {"nombre": "Inversiones Inmobiliarias",                              "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    32: {"nombre": "Activos Adquiridos en Arrendamiento Financiero",         "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    33: {"nombre": "Inmuebles, Maquinaria y Equipo",                         "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    34: {"nombre": "Intangibles",                                            "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    35: {"nombre": "Activos Biológicos",                                     "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    36: {"nombre": "Desvalorización de Activo Inmovilizado",                 "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    37: {"nombre": "Activo Diferido",                                        "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    38: {"nombre": "Otros Activos",                                          "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},
    39: {"nombre": "Depreciación, Amortización y Agotamiento Acumulados",    "grupo": "ACTIVO", "tipo": "ACTIVO NO CORRIENTE"},

    # ── PASIVO CORRIENTE ─────────────────────────────────────
    40: {"nombre": "Tributos y Aportes al Sistema de Pensiones y de Salud por Pagar", "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    41: {"nombre": "Remuneraciones y Participaciones por Pagar",             "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    42: {"nombre": "Cuentas por Pagar Comerciales - Terceros",               "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    43: {"nombre": "Cuentas por Pagar Comerciales - Relacionadas",           "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    44: {"nombre": "Cuentas por Pagar a los Accionistas, Directores y Gerentes", "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    45: {"nombre": "Obligaciones Financieras",                               "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    46: {"nombre": "Cuentas por Pagar Diversas - Terceros",                  "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    47: {"nombre": "Cuentas por Pagar Diversas - Relacionadas",              "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    48: {"nombre": "Provisiones",                                            "grupo": "PASIVO", "tipo": "PASIVO CORRIENTE"},
    49: {"nombre": "Pasivo Diferido",                                        "grupo": "PASIVO", "tipo": "PASIVO NO CORRIENTE"},

    # ── PATRIMONIO ───────────────────────────────────────────
    50: {"nombre": "Capital",                                                "grupo": "PATRIMONIO", "tipo": "PATRIMONIO"},
    51: {"nombre": "Acciones de Inversión",                                  "grupo": "PATRIMONIO", "tipo": "PATRIMONIO"},
    52: {"nombre": "Capital Adicional",                                      "grupo": "PATRIMONIO", "tipo": "PATRIMONIO"},
    56: {"nombre": "Resultados No Realizados",                               "grupo": "PATRIMONIO", "tipo": "PATRIMONIO"},
    57: {"nombre": "Excedente de Revaluación",                               "grupo": "PATRIMONIO", "tipo": "PATRIMONIO"},
    58: {"nombre": "Reservas",                                               "grupo": "PATRIMONIO", "tipo": "PATRIMONIO"},
    59: {"nombre": "Resultados Acumulados",                                  "grupo": "PATRIMONIO", "tipo": "PATRIMONIO"},

    # ── GASTOS ───────────────────────────────────────────────
    60: {"nombre": "Compras",                                                "grupo": "GASTOS", "tipo": "GASTO"},
    61: {"nombre": "Variación de Existencias",                               "grupo": "GASTOS", "tipo": "GASTO"},
    62: {"nombre": "Gastos de Personal, Directores y Gerentes",              "grupo": "GASTOS", "tipo": "GASTO"},
    63: {"nombre": "Gastos de Servicios Prestados por Terceros",             "grupo": "GASTOS", "tipo": "GASTO"},
    64: {"nombre": "Gastos por Tributos",                                    "grupo": "GASTOS", "tipo": "GASTO"},
    65: {"nombre": "Otros Gastos de Gestión",                                "grupo": "GASTOS", "tipo": "GASTO"},
    66: {"nombre": "Pérdida por Medición de Activos No Financieros al VR",   "grupo": "GASTOS", "tipo": "GASTO"},
    67: {"nombre": "Gastos Financieros",                                     "grupo": "GASTOS", "tipo": "GASTO"},
    68: {"nombre": "Valuación y Deterioro de Activos y Provisiones",         "grupo": "GASTOS", "tipo": "GASTO"},
    69: {"nombre": "Costo de Ventas",                                        "grupo": "GASTOS", "tipo": "GASTO"},

    # ── INGRESOS ─────────────────────────────────────────────
    70: {"nombre": "Ventas",                                                 "grupo": "INGRESOS", "tipo": "INGRESO"},
    71: {"nombre": "Variación de la Producción Almacenada",                  "grupo": "INGRESOS", "tipo": "INGRESO"},
    72: {"nombre": "Producción de Activo Inmovilizado",                      "grupo": "INGRESOS", "tipo": "INGRESO"},
    73: {"nombre": "Descuentos, Rebajas y Bonificaciones Obtenidos",         "grupo": "INGRESOS", "tipo": "INGRESO"},
    74: {"nombre": "Descuentos, Rebajas y Bonificaciones Concedidos",        "grupo": "INGRESOS", "tipo": "INGRESO"},
    75: {"nombre": "Otros Ingresos de Gestión",                              "grupo": "INGRESOS", "tipo": "INGRESO"},
    76: {"nombre": "Ganancia por Medición de Activos No Financieros al VR",  "grupo": "INGRESOS", "tipo": "INGRESO"},
    77: {"nombre": "Ingresos Financieros",                                   "grupo": "INGRESOS", "tipo": "INGRESO"},
    78: {"nombre": "Cargas Cubiertas por Provisiones",                       "grupo": "INGRESOS", "tipo": "INGRESO"},
    79: {"nombre": "Cargas Imputables a Cuentas de Costos y Gastos",         "grupo": "INGRESOS", "tipo": "INGRESO"},

    # ── CUENTAS DE CIERRE ────────────────────────────────────
    81: {"nombre": "Producción del Ejercicio",                               "grupo": "CIERRE", "tipo": "CIERRE"},
    82: {"nombre": "Valor Agregado",                                         "grupo": "CIERRE", "tipo": "CIERRE"},
    83: {"nombre": "Excedente Bruto o Insuficiencia Bruta de Explotación",   "grupo": "CIERRE", "tipo": "CIERRE"},
    84: {"nombre": "Resultado de Explotación",                               "grupo": "CIERRE", "tipo": "CIERRE"},
    85: {"nombre": "Resultado antes de Participaciones e Impuestos",         "grupo": "CIERRE", "tipo": "CIERRE"},
    87: {"nombre": "Participaciones de los Trabajadores",                    "grupo": "CIERRE", "tipo": "CIERRE"},
    88: {"nombre": "Impuesto a la Renta",                                    "grupo": "CIERRE", "tipo": "CIERRE"},
    89: {"nombre": "Determinación del Resultado del Ejercicio",              "grupo": "CIERRE", "tipo": "CIERRE"},

    # ── CUENTAS ANALÍTICAS ───────────────────────────────────
    91: {"nombre": "Costos por Distribuir",                                  "grupo": "ANALITICA", "tipo": "ANALITICA"},
    92: {"nombre": "Costos de Producción",                                   "grupo": "ANALITICA", "tipo": "ANALITICA"},
    93: {"nombre": "Centros de Costos",                                      "grupo": "ANALITICA", "tipo": "ANALITICA"},
    94: {"nombre": "Gastos Administrativos",                                 "grupo": "ANALITICA", "tipo": "ANALITICA"},
    95: {"nombre": "Gastos de Ventas",                                       "grupo": "ANALITICA", "tipo": "ANALITICA"},
    96: {"nombre": "Gastos Financieros",                                     "grupo": "ANALITICA", "tipo": "ANALITICA"},
}


# ── Alias comunes ────────────────────────────────────────────
# Mapea términos del enunciado → código de 2 dígitos
ALIAS_CUENTAS = {
    # Efectivo / Bancos
    "caja":                             10,
    "efectivo":                         10,
    "efectivo y equivalentes":          10,
    "efectivo y equivalentes de efectivo": 10,
    "banco":                            10,
    "bancos":                           10,
    "cuenta bancaria":                  10,
    "cuenta corriente":                 10,

    # Cuentas por cobrar
    "cuentas por cobrar":               12,
    "clientes":                         12,
    "facturas por cobrar":              12,
    "cuentas por cobrar comerciales":   12,

    # Existencias
    "mercaderías":                      20,
    "mercancias":                       20,
    "mercaderia":                       20,
    "inventario":                       20,
    "existencias":                      20,
    "productos terminados":             21,
    "materias primas":                  24,
    "suministros":                      25,
    "materiales auxiliares":            25,
    "envases":                          26,
    "embalajes":                        26,

    # Activo no corriente
    "terrenos":                         33,
    "edificios":                        33,
    "edificaciones":                    33,
    "maquinaria":                       33,
    "maquinaria y equipo":              33,
    "equipos":                          33,
    "muebles":                          33,
    "muebles y enseres":                33,
    "vehiculos":                        33,
    "vehículos":                        33,
    "inmuebles maquinaria y equipo":    33,
    "intangibles":                      34,
    "software":                         34,
    "depreciacion acumulada":           39,
    "depreciación acumulada":           39,

    # Pasivos
    "cuentas por pagar":                42,
    "proveedores":                      42,
    "cuentas por pagar comerciales":    42,
    "tributos por pagar":               40,
    "igv por pagar":                    40,
    "igv":                              40,
    "impuesto a la renta por pagar":    40,
    "impuesto a la renta":              40,
    "impuesto renta":                   40,
    "remuneraciones por pagar":         41,
    "sueldos por pagar":                41,
    "obligaciones financieras":         45,
    "prestamo bancario":                45,
    "préstamo bancario":                45,
    "prestamos bancarios":              45,
    "provisiones":                      48,

    # Patrimonio
    "capital":                          50,
    "capital social":                   50,
    "acciones de inversion":            51,
    "capital adicional":                52,
    "resultados acumulados":            59,
    "utilidades retenidas":             59,
    "perdidas acumuladas":              59,
    "reservas":                         58,
    "reserva legal":                    58,

    # Gastos
    "compras":                          60,
    "variacion de existencias":         61,
    "variacion de mercaderias":         61,
    "gastos de personal":               62,
    "sueldos":                          62,
    "salarios":                         62,
    "remuneraciones":                   62,
    "gastos de servicios":              63,
    "servicios de terceros":            63,
    "alquileres":                       63,
    "servicios basicos":                63,
    "agua":                             63,
    "luz":                              63,
    "energia electrica":                63,
    "telefono":                         63,
    "internet":                         63,
    "publicidad":                       63,
    "gastos por tributos":              64,
    "otros gastos":                     65,
    "seguros":                          65,
    "gastos financieros":               67,
    "intereses":                        67,
    "depreciacion":                     68,
    "depreciación":                     68,
    "amortizacion":                     68,
    "costo de ventas":                  69,

    # Ingresos
    "ventas":                           70,
    "ingresos por ventas":              70,
    "servicios":                        70,
    "ingresos por servicios":           70,
    "otros ingresos":                   75,
    "ingresos financieros":             77,
    "descuentos obtenidos":             73,
    "descuentos concedidos":            74,

    # Analíticas
    "gastos administrativos":           94,
    "gastos de administracion":         94,
    "gastos de ventas":                 95,
    "gastos financieros por funcion":   96,
}


def normalizar_codigo(codigo) -> int:
    """
    Recibe un código de cuenta (puede ser int o str con 2 o más dígitos)
    y lo normaliza a los primeros 2 dígitos.
    Ejemplo: 101 → 10, 4011 → 40, 6911 → 69, 70111 → 70
    """
    cod_str = str(int(codigo))
    cod_2 = int(cod_str[:2])
    return cod_2 if cod_2 in PLAN_CUENTAS else cod_2


def validar_codigo(codigo) -> bool:
    """Retorna True si el código (normalizado a 2 dígitos) existe en el plan."""
    return normalizar_codigo(codigo) in PLAN_CUENTAS


def buscar_cuenta_por_nombre(texto: str) -> list:
    """
    Busca cuentas cuyo nombre contenga el texto (sin importar mayúsculas).
    Retorna lista de (codigo, info).
    """
    texto = texto.lower().strip()
    return [
        (cod, info)
        for cod, info in PLAN_CUENTAS.items()
        if texto in info["nombre"].lower()
    ]


def obtener_info_cuenta(codigo: int) -> dict | None:
    """Retorna información de una cuenta por su código de 2 dígitos."""
    cod = normalizar_codigo(codigo)
    return PLAN_CUENTAS.get(cod)


def obtener_codigo_por_alias(alias: str) -> int | None:
    """Retorna el código de 2 dígitos a partir de un alias común."""
    return ALIAS_CUENTAS.get(alias.lower().strip())