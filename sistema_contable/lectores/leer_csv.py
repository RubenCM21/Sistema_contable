# ============================================================
# lectores/leer_csv.py
# Lee archivos CSV y extrae el contenido como texto
# ============================================================

import pandas as pd


def extraer_texto_csv(ruta_archivo: str) -> str:
    """
    Lee un archivo CSV y convierte su contenido a texto.
    Intenta detectar automáticamente el separador (coma o punto y coma).

    Retorna un string con todo el contenido, listo para enviar a Gemini.
    """
    try:
        # Intentar con coma primero, luego con punto y coma
        try:
            df = pd.read_csv(ruta_archivo, sep=',', header=None)
        except Exception:
            df = pd.read_csv(ruta_archivo, sep=';', header=None)

        # Eliminar filas y columnas vacías
        df = df.dropna(how='all').dropna(axis=1, how='all')

        if df.empty:
            raise ValueError("El archivo CSV no contiene datos legibles.")

        texto_total = ['=== ARCHIVO CSV ===']

        for _, fila in df.iterrows():
            valores = [str(v).strip() for v in fila if str(v).strip() not in ('', 'nan')]
            if valores:
                texto_total.append(' | '.join(valores))

        resultado = '\n'.join(texto_total)
        print(f"[OK] CSV leído correctamente → {len(texto_total)} líneas extraídas.")
        return resultado

    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise RuntimeError(f"Error al leer el CSV: {e}")


# ------------------------------------------------------------
# Prueba directa
# ------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python leer_csv.py <ruta_del_archivo.csv>")
    else:
        texto = extraer_texto_csv(sys.argv[1])
        print(texto)