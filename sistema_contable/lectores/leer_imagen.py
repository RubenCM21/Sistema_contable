# ============================================================
# lectores/leer_imagen.py
# Extrae texto de imágenes usando OCR (pytesseract)
#
# MEJORAS:
#   1. Preprocesamiento de imagen (escala grises, contraste,
#      binarización, upscaling) para mejor precisión OCR.
#   2. Corrección post-OCR de números con comas de miles
#      (ej. "50,000" leído como "50" → se restaura).
#   3. Múltiples configuraciones de Tesseract con fallback.
# ============================================================

import re
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import os


# --- CONFIGURACIÓN DE TESSERACT (Windows) ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuraciones de Tesseract ordenadas de más a menos agresiva
# --psm 6  = bloque de texto uniforme (mejor para enunciados)
# --psm 4  = columna única de texto de tamaño variable
# --oem 3  = motor LSTM (más preciso con números)
_CONFIGS_TESSERACT = [
    r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzáéíóúÁÉÍÓÚñÑüÜ.,:/%-() ',
    r'--oem 3 --psm 4',
    r'--oem 1 --psm 6',
]


# ─── Preprocesamiento de imagen ───────────────────────────────

def _preprocesar_imagen(imagen: Image.Image) -> Image.Image:
    """
    Aplica una cadena de transformaciones para mejorar la
    legibilidad del OCR, especialmente de números con comas.

    Pasos:
      1. Convertir a escala de grises
      2. Aumentar resolución (x2) — el paso MÁS importante
         para que Tesseract no confunda "50,000" con "50"
      3. Aumentar contraste
      4. Nitidez / sharpening
      5. Binarización adaptativa (umbral Otsu simulado)
    """
    # 1. Escala de grises
    img = imagen.convert('L')

    # 2. Upscaling x2.5 — la coma de miles es muy pequeña;
    #    agrandar la imagen la hace visible para Tesseract
    ancho, alto = img.size
    img = img.resize(
        (int(ancho * 2.5), int(alto * 2.5)),
        Image.LANCZOS
    )

    # 3. Aumentar contraste
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # 4. Nitidez
    img = ImageEnhance.Sharpness(img).enhance(2.5)
    img = img.filter(ImageFilter.SHARPEN)

    # 5. Binarización: convierte a blanco/negro para eliminar ruido
    img = img.point(lambda p: 255 if p > 140 else 0)

    return img


# ─── Corrección post-OCR de números ──────────────────────────

def _corregir_numeros(texto: str) -> str:
    """
    Corrige errores comunes de OCR con números contables:

    Problema 1 — Coma de miles truncada:
      Tesseract lee "50,000" como "50" o "50," o "50.000"
      → buscamos patrones como "50" seguido de espacios y
        más dígitos que deberian ser una sola cifra.

    Problema 2 — Punto como separador de miles:
      "50.000" → lo normalizamos a "50000" para que la IA
        no confunda con decimales.

    Problema 3 — Espacios dentro de números:
      "5 0 , 0 0 0" → "50,000"

    Problema 4 — 'O' (letra) confundida con '0' (cero)
      dentro de secuencias numéricas.
    """

    # ── Paso 1: Eliminar espacios dentro de secuencias numéricas
    # "5 0 0 0" → "5000"  |  "5 0, 0 0 0" → "50,000"
    texto = re.sub(r'(\d)\s+(\d)', r'\1\2', texto)
    # Aplicar varias veces por si hay múltiples espacios
    texto = re.sub(r'(\d)\s+(\d)', r'\1\2', texto)
    texto = re.sub(r'(\d)\s+(\d)', r'\1\2', texto)

    # ── Paso 2: 'O' mayúscula dentro de contexto numérico → '0'
    # "5O,OOO" → "50,000"
    texto = re.sub(r'(?<=\d)O(?=\d)', '0', texto)
    texto = re.sub(r'(?<=\d)O(?=[,.])', '0', texto)

    # ── Paso 3: Número seguido de coma suelta al final de línea
    # "50," → puede ser "50,000"; buscamos si la siguiente línea
    # empieza con 3 dígitos (los miles)
    texto = re.sub(
        r'(\d{1,3}),\s*\n\s*(\d{3})\b',
        r'\1,\2',
        texto
    )

    # ── Paso 4: Punto usado como separador de miles europeo
    # "50.000" → "50000" (en contexto peruano los decimales van con coma)
    # Solo si el patrón es NNN.NNN (exactamente 3 decimales = miles)
    texto = re.sub(
        r'\b(\d{1,3})\.(\d{3})\b',
        lambda m: m.group(1) + ',' + m.group(2),
        texto
    )

    # ── Paso 5: Números pegados a texto sin espacio
    # "50,000soles" → "50,000 soles"
    texto = re.sub(r'(\d)([A-Za-záéíóúÁÉÍÓÚñÑ])', r'\1 \2', texto)
    texto = re.sub(r'([A-Za-záéíóúÁÉÍÓÚñÑ])(\d)', r'\1 \2', texto)

    return texto


# ─── Función principal ────────────────────────────────────────

def extraer_texto_imagen(ruta_archivo: str) -> str:
    """
    Aplica OCR a una imagen y extrae el texto contenido en ella.
    Soporta PNG, JPG, JPEG, BMP, TIFF, WEBP.

    Incluye preprocesamiento para mejorar la lectura de números
    con comas de miles (ej. 50,000 — problema frecuente en
    enunciados contables fotografiados o escaneados).

    Retorna el texto extraído y corregido como string.
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")

    try:
        imagen_original = Image.open(ruta_archivo)

        # ── Intentar con imagen preprocesada primero ──────────
        imagen_proc = _preprocesar_imagen(imagen_original)

        texto = ""
        config_usada = ""

        for config in _CONFIGS_TESSERACT:
            try:
                texto_candidato = pytesseract.image_to_string(
                    imagen_proc,
                    lang='spa+eng',
                    config=config
                ).strip()

                # Preferir el resultado con más caracteres numéricos
                if len(texto_candidato) > len(texto):
                    texto = texto_candidato
                    config_usada = config

                if texto and len(texto) > 30:
                    break   # resultado suficientemente bueno

            except Exception:
                continue

        # ── Fallback: imagen original sin preprocesar ─────────
        if not texto or len(texto) < 10:
            texto = pytesseract.image_to_string(
                imagen_original,
                lang='spa+eng',
                config=r'--oem 3 --psm 6'
            ).strip()

        if not texto:
            raise ValueError(
                "No se pudo extraer texto de la imagen. "
                "Verifica que tenga buena resolución y el texto sea legible."
            )

        # ── Corrección de números ──────────────────────────────
        texto_corregido = _corregir_numeros(texto)

        lineas = len(texto_corregido.splitlines())
        print(f"[OK] Imagen procesada con OCR → {lineas} líneas extraídas "
              f"(config: {config_usada.strip()[:30]}...)")

        return f"=== TEXTO EXTRAÍDO DE IMAGEN ===\n{texto_corregido}"

    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error al procesar la imagen: {e}")


# ─── Prueba directa ───────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python leer_imagen.py <ruta_de_la_imagen>")
        print("Ejemplo: python leer_imagen.py enunciado.png")
    else:
        try:
            resultado = extraer_texto_imagen(sys.argv[1])
            print("\n" + "="*50)
            print(resultado)
            print("="*50)
        except Exception as e:
            print(f"[ERROR] {e}")