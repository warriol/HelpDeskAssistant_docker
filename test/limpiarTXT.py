# python limpiarTXT.py .\txt\nombre.txt
import re
import sys
import unicodedata

def limpiar_texto_legal(ruta_archivo):
    # 1. Intentamos leer con detección de errores
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except UnicodeDecodeError:
        with open(ruta_archivo, 'r', encoding='latin-1') as f:
            contenido = f.read()

    # 2. Reemplazos manuales de símbolos que fallan en JSON
    contenido = contenido.replace('“', '"').replace('”', '"').replace('—', '-')

    # 3. LO MÁS IMPORTANTE: Normalizar para asegurar que las tildes sean estándar
    # Esto une caracteres acentuados que puedan estar divididos
    contenido = unicodedata.normalize('NFC', contenido)

    # 4. Limpieza: Permitimos caracteres latinos (tildes y ñ) explícitamente
    # Borramos caracteres de control invisibles (0-31) que son los que rompen el stream
    contenido = "".join(ch for ch in contenido if unicodedata.category(ch)[0] != 'C' or ch in '\n\t')

    with open(ruta_archivo + "_limpio.txt", 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"Archivo {ruta_archivo} sanitizado con éxito.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ruta_archivo = sys.argv[1]
        limpiar_texto_legal(ruta_archivo)
    else:
        print("Error: Falta el nombre del archivo. Ejemplo: python limpiarTXT.py ./txt/leyes.txt")