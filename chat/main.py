"""
Punto de entrada del cliente de chat P2P.

Conecta la capa de red (ChatNetwork) con la interfaz gráfica (ChatGUI)
y arranca la aplicación.
"""

from tkinter import messagebox

from .gui import ChatGUI           # Relativo: gui.py está en el mismo paquete chat/
from .network import ChatNetwork   # Relativo: network.py está en el mismo paquete chat/


def main():
    net = ChatNetwork()

    if not net.connect_to_registry():
        messagebox.showerror("Error", "No se pudo conectar al servidor de registro.")
        return

    app = ChatGUI(net)
    app.show_login()


if __name__ == "__main__":
    main()
