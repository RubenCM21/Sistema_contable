# ============================================================
# lectores/leer_voz.py
# Convierte audio a texto usando SpeechRecognition
# ============================================================

import speech_recognition as sr
from pydub import AudioSegment
import os


def convertir_a_wav(ruta_archivo: str) -> str:
    """
    Convierte cualquier formato de audio a WAV temporal.
    SpeechRecognition solo trabaja con WAV nativamente.
    Retorna la ruta del archivo WAV generado.
    """
    ruta_wav = ruta_archivo.rsplit('.', 1)[0] + '_temp.wav'
    extension = ruta_archivo.rsplit('.', 1)[-1].lower()

    if extension == 'wav':
        return ruta_archivo  # ya es WAV, no necesita conversión

    audio = AudioSegment.from_file(ruta_archivo, format=extension)
    audio.export(ruta_wav, format='wav')
    return ruta_wav


def extraer_texto_voz(ruta_archivo: str) -> str:
    """
    Convierte un archivo de audio a texto.
    Usa Google Speech Recognition (gratuito, requiere internet).
    Soporta MP3, WAV, OGG, M4A, FLAC.

    Retorna el texto transcrito como string.
    """
    reconocedor = sr.Recognizer()
    ruta_wav    = None

    try:
        # Convertir a WAV si es necesario
        ruta_wav = convertir_a_wav(ruta_archivo)

        with sr.AudioFile(ruta_wav) as fuente:
            # Ajuste de ruido ambiente
            reconocedor.adjust_for_ambient_noise(fuente, duration=0.5)
            audio = reconocedor.record(fuente)

        # Transcripción en español
        texto = reconocedor.recognize_google(audio, language='es-PE')
        texto = texto.strip()

        if not texto:
            raise ValueError("No se detectó voz en el archivo de audio.")

        print(f"[OK] Audio transcrito correctamente → {len(texto.split())} palabras detectadas.")
        return f"=== TEXTO TRANSCRITO DE AUDIO ===\n{texto}"

    except sr.UnknownValueError:
        raise ValueError(
            "No se pudo entender el audio. "
            "Verifica que haya voz clara y sin demasiado ruido de fondo."
        )
    except sr.RequestError as e:
        raise RuntimeError(
            f"Error al conectar con el servicio de transcripción: {e}. "
            f"Verifica tu conexión a internet."
        )
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise RuntimeError(f"Error al procesar el audio: {e}")
    finally:
        # Eliminar el WAV temporal si se creó
        if ruta_wav and ruta_wav != ruta_archivo and os.path.exists(ruta_wav):
            os.remove(ruta_wav)


# ------------------------------------------------------------
# Prueba directa
# ------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python leer_voz.py <ruta_del_audio>")
    else:
        texto = extraer_texto_voz(sys.argv[1])
        print(texto)