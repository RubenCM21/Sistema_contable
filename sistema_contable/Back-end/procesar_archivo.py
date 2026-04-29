# ============================================================
# procesar_archivo.py
# Router FastAPI — POST /api/procesar-archivo
#
# CORRECCIÓN: los lectores exponen funciones con nombres
#   extraer_texto_csv, extraer_texto_excel, etc.
#   (NO "leer"). Este archivo los llama correctamente.
# ============================================================

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from interpretador import interpretar_texto
from libro_diario import registrar_asientos_desde_interpretacion

router = APIRouter(prefix="/api", tags=["Archivos"])

# ─── Extensiones soportadas ──────────────────────────────────
EXTENSIONES_EXCEL  = {".xlsx", ".xls"}
EXTENSIONES_PDF    = {".pdf"}
EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
EXTENSIONES_AUDIO  = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
EXTENSIONES_CSV    = {".csv"}

TODAS_EXTENSIONES = (
    EXTENSIONES_EXCEL | EXTENSIONES_PDF |
    EXTENSIONES_IMAGEN | EXTENSIONES_AUDIO | EXTENSIONES_CSV
)


def _extension(filename: str) -> str:
    """Retorna la extensión en minúsculas, ej. '.pdf'"""
    return os.path.splitext(filename.lower())[1]


def _leer_archivo(ruta_temporal: str, ext: str) -> str:
    """
    Llama a la función correcta de cada lector según la extensión.
    Cada lector expone su función con el nombre real:
        extraer_texto_excel / extraer_texto_csv /
        extraer_texto_pdf   / extraer_texto_imagen / extraer_texto_voz
    """
    if ext in EXTENSIONES_EXCEL:
        from lectores.leer_excel import extraer_texto_excel
        return extraer_texto_excel(ruta_temporal)

    if ext in EXTENSIONES_PDF:
        from lectores.leer_pdf import extraer_texto_pdf
        return extraer_texto_pdf(ruta_temporal)

    if ext in EXTENSIONES_IMAGEN:
        from lectores.leer_imagen import extraer_texto_imagen
        return extraer_texto_imagen(ruta_temporal)

    if ext in EXTENSIONES_AUDIO:
        from lectores.leer_voz import extraer_texto_voz
        return extraer_texto_voz(ruta_temporal)

    if ext in EXTENSIONES_CSV:
        from lectores.leer_csv import extraer_texto_csv
        return extraer_texto_csv(ruta_temporal)

    raise HTTPException(
        status_code=415,
        detail=(
            f"Tipo de archivo no soportado: '{ext}'. "
            f"Formatos válidos: xlsx, xls, csv, pdf, "
            f"png, jpg, jpeg, bmp, tiff, webp, mp3, wav, ogg, m4a, flac"
        )
    )


# ─── Endpoint ────────────────────────────────────────────────
@router.post("/procesar-archivo")
async def procesar_archivo(archivo: UploadFile = File(...)):
    """
    Recibe un archivo, extrae su texto y lo interpreta con IA.

    Flujo:
      1. Valida la extensión.
      2. Guarda el archivo en un directorio temporal.
      3. Extrae el texto con el lector correspondiente.
      4. Interpreta el texto con la IA (Gemini).
      5. Guarda los asientos en la BD.
      6. Devuelve el resultado completo.
    """
    ext = _extension(archivo.filename)

    if ext not in TODAS_EXTENSIONES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Formato '{ext}' no soportado. "
                f"Usa: xlsx, xls, csv, pdf, png, jpg, jpeg, bmp, tiff, webp, "
                f"mp3, wav, ogg, m4a, flac"
            )
        )

    # Guardar en disco temporalmente manteniendo la extensión original
    contenido = await archivo.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(contenido)
        ruta_tmp = tmp.name

    try:
        # ── 1. Extraer texto ───────────────────────────────────
        texto_extraido = _leer_archivo(ruta_tmp, ext)

        if not texto_extraido or not texto_extraido.strip():
            raise HTTPException(
                status_code=422,
                detail=(
                    "No se pudo extraer texto del archivo. "
                    "Verifica que el archivo tenga contenido legible."
                )
            )

        # ── 2. Interpretar con IA ──────────────────────────────
        interpretacion = interpretar_texto(texto_extraido)

        if "error" in interpretacion and not interpretacion.get("asientos"):
            raise HTTPException(
                status_code=422,
                detail=interpretacion["error"]
            )

        # ── 3. Guardar asientos en BD ──────────────────────────
        detalle_guardado = None
        if interpretacion.get("asientos"):
            detalle_guardado = registrar_asientos_desde_interpretacion(
                interpretacion["asientos"]
            )

        return {
            "archivo": archivo.filename,
            "extension": ext,
            "texto_extraido_preview": (
                texto_extraido[:600] + "..."
                if len(texto_extraido) > 600
                else texto_extraido
            ),
            "interpretacion": interpretacion,
            "guardado": detalle_guardado is not None,
            "detalle_guardado": detalle_guardado,
        }

    except HTTPException:
        raise  # Re-lanzar errores HTTP tal cual
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, RuntimeError) as e:
        # Errores conocidos de los lectores
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado al procesar el archivo: {str(e)}"
        )
    finally:
        # Siempre limpiar el archivo temporal
        try:
            os.unlink(ruta_tmp)
        except Exception:
            pass