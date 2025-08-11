# Este script corrige la codificación de un archivo a UTF-8.
# Para usarlo, guárdalo como 'fix_encoding.py' y ejecútalo desde tu terminal.

import sys
import os

def convert_to_utf8(filename):
    """
    Lee un archivo con una codificación supuesta (latin-1) y lo reescribe como UTF-8.
    Crea una copia de seguridad del archivo original antes de la conversión, eliminando la antigua si existe.
    """
    try:
        backup_filename = f"{filename}.bak"
        
        # Elimina el archivo de copia de seguridad antiguo si ya existe
        if os.path.exists(backup_filename):
            os.remove(backup_filename)
            print(f"Archivo de copia de seguridad anterior '{backup_filename}' eliminado.")

        # Crea una copia de seguridad del archivo original
        os.rename(filename, backup_filename)
        print(f"Copia de seguridad del archivo original creada en '{backup_filename}'")

        # Lee el contenido del archivo con la codificación probable
        with open(backup_filename, 'r', encoding='latin-1') as infile:
            content = infile.read()

        # Escribe el contenido en un nuevo archivo con codificación UTF-8
        with open(filename, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

        print(f"✅ Archivo '{filename}' convertido a UTF-8 exitosamente.")
        return True
    except FileNotFoundError:
        print(f"⚠️ Error: Archivo '{filename}' no encontrado.")
        return False
    except Exception as e:
        print(f"❌ Ocurrió un error al convertir el archivo: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python fix_encoding.py <nombre_del_archivo>")
        sys.exit(1)

    # El primer argumento de la línea de comandos es el nombre del archivo a convertir
    target_file = sys.argv[1]
    convert_to_utf8(target_file)
