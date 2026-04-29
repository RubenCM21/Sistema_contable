# ============================================================
# lectores/leer_pdf.py
# Lee archivos PDF y extrae el texto
# ============================================================

import pdfplumber


def extraer_texto_pdf(ruta_archivo: str) -> str:
    """
    Lee un archivo PDF página por página y extrae todo el texto.
    Funciona con PDFs de texto nativo.
    Si el PDF es una imagen escaneada, el texto puede ser limitado
    — en ese caso se recomienda subir la imagen directamente.

    Retorna un string con todo el texto extraído.
    """
    try:
        texto_total = []

        with pdfplumber.open(ruta_archivo) as pdf:
            total_paginas = len(pdf.pages)

            for i, pagina in enumerate(pdf.pages, start=1):
                texto_pagina = pagina.extract_text()

                if texto_pagina and texto_pagina.strip():
                    texto_total.append(f"=== PÁGINA {i}/{total_paginas} ===")
                    texto_total.append(texto_pagina.strip())

        if not texto_total:
            raise ValueError(
                "No se pudo extraer texto del PDF. "
                "Si es un PDF escaneado, súbelo como imagen (PNG o JPG)."
            )

        resultado = '\n'.join(texto_total)
        print(f"[OK] PDF leído correctamente → {total_paginas} página(s) procesada(s).")
        return resultado

    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise RuntimeError(f"Error al leer el PDF: {e}")


# ------------------------------------------------------------
# Prueba directa
# ------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python leer_pdf.py <ruta_del_archivo.pdf>")
    else:
        texto = extraer_texto_pdf(sys.argv[1])
        print(texto)