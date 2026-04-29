# ============================================================
# lectores/leer_excel.py
# Lee archivos Excel y extrae el contenido como texto
# para enviarlo al interpretador de IA
# ============================================================

import pandas as pd


def extraer_texto_excel(ruta_archivo: str) -> str:
    """
    Lee un archivo Excel y convierte su contenido a texto narrativo.
    Soporta archivos con una o múltiples hojas.

    Retorna un string con todo el contenido, listo para enviar a Gemini.
    """
    try:
        # Leer todas las hojas del archivo
        hojas = pd.read_excel(ruta_archivo, sheet_name=None, header=None)

        texto_total = []

        for nombre_hoja, df in hojas.items():
            # Eliminar filas y columnas completamente vacías
            df = df.dropna(how='all').dropna(axis=1, how='all')

            if df.empty:
                continue

            texto_total.append(f"=== HOJA: {nombre_hoja} ===")

            # Convertir cada fila a texto
            for _, fila in df.iterrows():
                valores = [str(v).strip() for v in fila if str(v).strip() not in ('', 'nan')]
                if valores:
                    texto_total.append(' | '.join(valores))

        if not texto_total:
            raise ValueError("El archivo Excel no contiene datos legibles.")

        resultado = '\n'.join(texto_total)
        print(f"[OK] Excel leído correctamente → {len(texto_total)} líneas extraídas.")
        return resultado

    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise RuntimeError(f"Error al leer el Excel: {e}")


# ------------------------------------------------------------
# Prueba directa
# ------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python leer_excel.py <ruta_del_archivo.xlsx>")
    else:
        texto = extraer_texto_excel(sys.argv[1])
        print(texto)