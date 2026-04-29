# ============================================================
# lectores/leer_imagen.py
# Extrae texto de imágenes usando OCR (pytesseract)
# ============================================================

import pytesseract
from PIL import Image
import os


# --- CONFIGURACIÓN DE TESSERACT ---
# Si estás en Windows, descomenta y ajusta esta línea
# con la ruta donde instalaste Tesseract:

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extraer_texto_imagen(ruta_archivo: str) -> str:
    """
    Aplica OCR a una imagen y extrae el texto contenido en ella.
    Soporta PNG, JPG, JPEG, BMP, TIFF, WEBP.

    Retorna el texto extraído como string.
    """
    try:
        imagen = Image.open(ruta_archivo)

        # OCR en español e inglés para mayor precisión
        texto = pytesseract.image_to_string(imagen, lang='spa+eng')

        texto = texto.strip()

        if not texto:
            raise ValueError(
                "No se pudo extraer texto de la imagen. "
                "Verifica que la imagen tenga buena resolución y el texto sea legible."
            )

        print(f"[OK] Imagen procesada con OCR → {len(texto.splitlines())} líneas extraídas.")
        return f"=== TEXTO EXTRAÍDO DE IMAGEN ===\n{texto}"

    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise RuntimeError(f"Error al procesar la imagen: {e}")


# ------------------------------------------------------------
# Prueba directa
# ------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python leer_imagen.py <ruta_de_la_imagen>")
    else:
        texto = extraer_texto_imagen(sys.argv[1])
        print(texto)