import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import io

from interpretador import interpretar_texto
from libro_diario import (
    registrar_asientos_desde_interpretacion,
    obtener_libro_diario,
    obtener_resumen_diario
)
from libro_mayor import obtener_mayor_agrupado, obtener_libro_mayor
from balance_comprobacion import (
    obtener_balance_comprobacion,
    obtener_historial_balances,
    obtener_detalle_balance
)
from estado_situacion_financiera import obtener_estado_situacion_financiera
from estado_resultados import obtener_estado_resultados
from exportar import exportar_excel, exportar_pdf
from plan_cuentas import PLAN_CUENTAS, normalizar_codigo
from conexion_bd import insertar_cuenta
from procesar_archivo import router as archivo_router

app = FastAPI(
    title="Sistema Contable API",
    description="API backend para el sistema contable automatizado",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(archivo_router)


# ── Modelos ───────────────────────────────────────────────────
class TextoRequest(BaseModel):
    texto: str
    guardar: bool = True

class TextoContableRequest(BaseModel):
    texto: str
    guardar: bool = True


# ── Startup ───────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("[Startup] Sincronizando plan de cuentas (2 dígitos) en BD...")
    for cod, info in PLAN_CUENTAS.items():
        insertar_cuenta(
            cod_cuenta    = cod,
            nombre_cuenta = info["nombre"],
            grupo_cuenta  = info["grupo"],
            tipo_cuenta   = info["tipo"]
        )
    print(f"[Startup] {len(PLAN_CUENTAS)} cuentas sincronizadas.")


# ── Health ────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
def health():
    from conexion_bd import obtener_conexion, cerrar_conexion
    conexion = obtener_conexion()
    bd_ok    = conexion is not None
    if conexion:
        cerrar_conexion(conexion)
    return {"estado": "OK" if bd_ok else "ERROR",
            "bd": "conectada" if bd_ok else "sin conexión",
            "version": "1.0.0"}


# ════════════════════════════════════════════════════════════
# ENDPOINTS FRONTEND (/api/...)
# ════════════════════════════════════════════════════════════

@app.post("/api/procesar-texto", tags=["Contabilización"])
def api_procesar_texto(request: TextoRequest):
    """Endpoint usado por el frontend para procesar texto directo."""
    if not request.texto.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")

    interpretacion = interpretar_texto(request.texto)

    if "error" in interpretacion and not interpretacion.get("asientos"):
        raise HTTPException(status_code=422, detail=interpretacion["error"])

    asientos = interpretacion.get("asientos", [])
    errores  = 0

    if request.guardar and asientos:
        detalle = registrar_asientos_desde_interpretacion(asientos)
        errores = detalle.get("errores", 0)

    return {
        "total_asientos": len(asientos),
        "asientos":       asientos,
        "errores":        errores,
        "guardado":       request.guardar
    }


@app.get("/api/libro-diario", tags=["Libros Contables"])
def api_libro_diario(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin:    Optional[str] = Query(None)
):
    return obtener_libro_diario(fecha_inicio, fecha_fin)


@app.get("/api/libro-mayor", tags=["Libros Contables"])
def api_libro_mayor(cod_cuenta: Optional[int] = Query(None)):
    if cod_cuenta:
        return obtener_libro_mayor(normalizar_codigo(cod_cuenta))
    return obtener_mayor_agrupado()


@app.get("/api/balance-comprobacion", tags=["Estados Financieros"])
def api_balance(
    mes:  Optional[int] = Query(None),
    anio: Optional[int] = Query(None)
):
    return obtener_balance_comprobacion(mes, anio)


@app.get("/api/estado-situacion-financiera", tags=["Estados Financieros"])
def api_esf(fecha_corte: Optional[str] = Query(None)):
    return obtener_estado_situacion_financiera(fecha_corte)


@app.get("/api/estado-resultados", tags=["Estados Financieros"])
def api_er(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin:    Optional[str] = Query(None)
):
    datos = obtener_estado_resultados(fecha_inicio, fecha_fin)
    if "error" in datos:
        raise HTTPException(status_code=500, detail=datos["error"])
    return datos


@app.get("/api/exportar/excel", tags=["Exportación"])
def api_excel(tablas: Optional[str] = Query(None)):
    lista = [t.strip() for t in tablas.split(",")] if tablas else None
    contenido = exportar_excel(lista)
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=sistema_contable.xlsx"}
    )


@app.get("/api/exportar/pdf", tags=["Exportación"])
def api_pdf(tablas: Optional[str] = Query(None)):
    lista = [t.strip() for t in tablas.split(",")] if tablas else None
    contenido = exportar_pdf(lista)
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=sistema_contable.pdf"}
    )


# ════════════════════════════════════════════════════════════
# ENDPOINTS POSTMAN (/interpretar, /diario, etc.)
# ════════════════════════════════════════════════════════════

@app.post("/interpretar", tags=["Contabilización"])
def interpretar_y_registrar(request: TextoContableRequest):
    if not request.texto.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")

    interpretacion = interpretar_texto(request.texto)

    if "error" in interpretacion and not interpretacion.get("asientos"):
        raise HTTPException(status_code=422, detail=interpretacion["error"])

    resultado = {"interpretacion": interpretacion, "guardado": False, "detalle_guardado": None}

    if request.guardar and interpretacion.get("asientos"):
        detalle = registrar_asientos_desde_interpretacion(interpretacion["asientos"])
        resultado["guardado"]         = True
        resultado["detalle_guardado"] = detalle

    return resultado


@app.get("/diario", tags=["Libros Contables"])
def libro_diario(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin:    Optional[str] = Query(None)
):
    datos   = obtener_libro_diario(fecha_inicio, fecha_fin)
    resumen = obtener_resumen_diario()
    return {"total_registros": len(datos), "resumen": resumen, "datos": datos}


@app.get("/mayor", tags=["Libros Contables"])
def libro_mayor_completo():
    datos = obtener_mayor_agrupado()
    return {"total_cuentas": len(datos), "cuentas": datos}


@app.get("/mayor/{cod_cuenta}", tags=["Libros Contables"])
def libro_mayor_cuenta(cod_cuenta: int):
    cod_2 = normalizar_codigo(cod_cuenta)
    datos = obtener_libro_mayor(cod_2)
    if not datos:
        raise HTTPException(status_code=404, detail=f"Sin movimientos para cuenta {cod_2}")
    return {"cod_cuenta": cod_2, "total_movimientos": len(datos), "movimientos": datos}


@app.get("/balance", tags=["Estados Financieros"])
def balance_comprobacion(
    mes:  Optional[int] = Query(None),
    anio: Optional[int] = Query(None)
):
    return obtener_balance_comprobacion(mes, anio)


@app.get("/balance/historial", tags=["Estados Financieros"])
def historial_balances():
    return {"balances": obtener_historial_balances()}


@app.get("/balance/{cod_balance}", tags=["Estados Financieros"])
def detalle_balance(cod_balance: int):
    datos = obtener_detalle_balance(cod_balance)
    if "error" in datos:
        raise HTTPException(status_code=404, detail=datos["error"])
    return datos


@app.get("/situacion", tags=["Estados Financieros"])
def estado_situacion(fecha_corte: Optional[str] = Query(None)):
    return obtener_estado_situacion_financiera(fecha_corte)


@app.get("/resultados", tags=["Estados Financieros"])
def estado_resultados(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin:    Optional[str] = Query(None)
):
    datos = obtener_estado_resultados(fecha_inicio, fecha_fin)
    if "error" in datos:
        raise HTTPException(status_code=500, detail=datos["error"])
    return datos


@app.get("/exportar/excel", tags=["Exportación"])
def descargar_excel(tablas: Optional[str] = Query(None)):
    lista = [t.strip() for t in tablas.split(",")] if tablas else None
    contenido = exportar_excel(lista)
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=sistema_contable.xlsx"}
    )


@app.get("/exportar/pdf", tags=["Exportación"])
def descargar_pdf(tablas: Optional[str] = Query(None)):
    lista = [t.strip() for t in tablas.split(",")] if tablas else None
    contenido = exportar_pdf(lista)
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=sistema_contable.pdf"}
    )


@app.get("/cuentas", tags=["Catálogo"])
def listar_cuentas(buscar: Optional[str] = None):
    resultado = []
    for cod, info in sorted(PLAN_CUENTAS.items()):
        if buscar and buscar.lower() not in info["nombre"].lower():
            continue
        resultado.append({"codigo": cod, "nombre": info["nombre"],
                           "grupo": info["grupo"], "tipo": info["tipo"]})
    return {"total": len(resultado), "cuentas": resultado}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)