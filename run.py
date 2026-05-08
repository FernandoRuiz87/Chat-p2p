"""
Lanzador principal del cliente de chat.

Ejecutar desde la raíz del proyecto:
    python run.py

Al ejecutarlo desde la raíz, Python agrega la raíz al sys.path,
lo que permite que todos los imports absolutos (config, crypto) funcionen.
"""

from chat.main import main

if __name__ == "__main__":
    main()
