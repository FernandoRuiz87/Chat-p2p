"""
Módulo de interfaz gráfica (Tkinter + CustomTkinter).

Construye la ventana de login y la ventana principal del chat.
Toda interacción con la red se delega a una instancia de ChatNetwork
a través de llamadas directas y callbacks registrados en __init__.
"""

import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from PIL import Image, ImageTk
from customtkinter import CTkButton, CTkEntry

from config import config          # Absoluto: config/ está en la raíz del proyecto
from .network import ChatNetwork   # Relativo: network.py está en el mismo paquete chat/


class ChatGUI:
    """
    Gestiona toda la interfaz gráfica del cliente de chat.

    Recibe una instancia de ChatNetwork y registra los callbacks
    necesarios para que la red pueda actualizar la UI al recibir eventos.
    """

    def __init__(self, network: ChatNetwork):
        self._net = network

        # Ventana raíz (login). Se guarda para poder ocultarla al abrir el chat.
        self._login_win: tk.Tk | None = None

        # Widgets del chat que se actualizan desde los callbacks de red
        self.chat_text: scrolledtext.ScrolledText | None = None
        self.peers_listbox: tk.Listbox | None = None
        self.message_box: tk.Text | None = None

        # Registrar callbacks: la red llama a estos métodos al recibir eventos
        network.on_message = self.add_message
        network.on_peer_list_changed = self.refresh_peer_list
        network.on_image_received = lambda path: self.show_image(path, "recibida")

    # ------------------------------------------------------------------
    # Ventana de login
    # ------------------------------------------------------------------

    def show_login(self):
        """Construye y muestra la ventana de login."""
        win = tk.Tk()
        self._login_win = win
        win.title("Chat")
        win.configure(bg=config.COLOR_BG_DARK)
        win.resizable(False, False)

        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x = (sw - config.LOGIN_W) // 2
        y = (sh - config.LOGIN_H) // 2
        win.geometry(f"{config.LOGIN_W}x{config.LOGIN_H}+{x}+{y}")

        icon = tk.PhotoImage(file=config.ICON_PATH)
        win.iconphoto(True, icon)

        win.columnconfigure(0, weight=1)
        for row, weight in enumerate([15, 15, 8, 5]):
            win.rowconfigure(row, weight=weight)

        # Logo
        logo = tk.PhotoImage(file=config.ICON_PATH, master=win)
        tk.Label(win, image=logo, bg=config.COLOR_BG_DARK).grid(row=0, column=0)

        # Separador decorativo con título
        canvas = tk.Canvas(win, bg=config.COLOR_BG_DARK, height=20, highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew")
        canvas.create_line(25, 0, 300, 0, fill=config.COLOR_TEXT_WHITE, width=1)
        canvas.create_text(162.5, 30, text="CHAT", fill=config.COLOR_TEXT_WHITE, font=config.FONT_TITLE)
        canvas.create_line(25, 52, 300, 52, fill=config.COLOR_TEXT_WHITE, width=1)

        tk.Label(
            win,
            text="Ingrese su nombre de usuario",
            background=config.COLOR_BG_DARK,
            foreground=config.COLOR_TEXT_WHITE,
            font=config.FONT_TITLE,
            justify="center",
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=25, pady=(0, 80))

        entry = CTkEntry(master=win, height=24, width=275, corner_radius=5)
        entry.grid(row=2, column=0, sticky="we", padx=25)

        CTkButton(
            master=win,
            text="Ingresar",
            width=275,
            corner_radius=10,
            fg_color=config.COLOR_ACCENT,
            text_color=config.COLOR_TEXT_WHITE,
            hover_color=config.COLOR_ACCENT_HOVER,
            command=lambda: self._on_login(entry),
        ).grid(row=3, column=0, columnspan=2, sticky="we", padx=25, pady=(0, 30))

        entry.bind("<Return>", lambda _: self._on_login(entry))

        win.mainloop()

    def _on_login(self, entry: CTkEntry):
        """Valida el nombre ingresado e intenta registrar el nodo en el servidor."""
        name = entry.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre de usuario no puede quedar vacío")
            return
        if not self._net.register_node(name):
            messagebox.showerror("Error", "No se pudo registrar en el servidor")
            return
        messagebox.showinfo("¡Bienvenido!", "Tu registro ha sido exitoso.")
        self._login_win.withdraw()
        self.show_chat()

    # ------------------------------------------------------------------
    # Ventana principal de chat
    # ------------------------------------------------------------------

    def show_chat(self):
        """Construye la ventana principal del chat."""
        win = tk.Toplevel()
        win.title(f"CHAT - {self._net.name.upper()}#{self._net.port}")
        win.configure(bg=config.COLOR_BG_DARK)

        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x = (sw - config.CHAT_W) // 2
        y = (sh - config.CHAT_H) // 2
        win.geometry(f"{config.CHAT_W}x{config.CHAT_H}+{x}+{y}")
        win.minsize(config.CHAT_MIN_W, config.CHAT_MIN_H)

        icon = tk.PhotoImage(file=config.ICON_PATH)
        win.iconphoto(True, icon)

        main_frame = tk.Frame(win)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._build_sidebar(main_frame)
        self._build_chat_area(main_frame)

        win.protocol("WM_DELETE_WINDOW", lambda: self._on_closing(win))

        # Iniciar red: conectar con peers e iniciar el servidor P2P de este nodo
        self._net.connect_to_peers()
        threading.Thread(target=self._net.start_node_server, daemon=True).start()

        win.mainloop()

    def _build_sidebar(self, parent: tk.Frame):
        """Construye la barra lateral con nombre de usuario y lista de peers."""
        sidebar = tk.Frame(parent, bg=config.COLOR_BG_DARK, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            sidebar,
            text=f"¡Hola {self._net.name}!",
            font=config.FONT_LARGE,
            foreground=config.COLOR_TEXT_USER,
            background=config.COLOR_BG_DARK,
        ).pack(fill=tk.X, padx=50, pady=5)

        tk.Label(
            sidebar,
            text="● Usuarios conectados",
            font=config.FONT_PEERS,
            foreground=config.COLOR_ONLINE,
            background=config.COLOR_BG_DARK,
        ).pack(fill=tk.X, pady=5)

        self.peers_listbox = tk.Listbox(
            sidebar,
            bg=config.COLOR_BG_DARK,
            fg=config.COLOR_TEXT_GREEN,
            font=config.FONT_MAIN,
            selectbackground=config.COLOR_BG_MID,
            highlightbackground=config.COLOR_BG_LIGHT,
            highlightcolor=config.COLOR_TEXT_GREEN,
            bd=0,
        )
        self.peers_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.refresh_peer_list()

    def _build_chat_area(self, parent: tk.Frame):
        """Construye el área de mensajes y el panel de entrada de texto."""
        right = tk.Frame(parent, bg=config.COLOR_BG_LIGHT)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Barra superior decorativa
        tk.Frame(right, bg=config.COLOR_BG_MID, height=60).pack(fill=tk.X)

        # Área de mensajes (solo lectura; se habilita temporalmente para escribir)
        self.chat_text = scrolledtext.ScrolledText(
            right,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=config.COLOR_BG_MID,
            font=config.FONT_MAIN,
            foreground=config.COLOR_TEXT_WHITE,
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Colores por tipo de mensaje
        self.chat_text.tag_configure("peer",     foreground=config.COLOR_MSG_PEER)
        self.chat_text.tag_configure("self",     foreground=config.COLOR_MSG_SELF, justify="right")
        self.chat_text.tag_configure("new_user", foreground=config.COLOR_MSG_JOIN)
        self.chat_text.tag_configure("leave",    foreground=config.COLOR_MSG_LEAVE)

        # Panel de entrada
        input_frame = tk.Frame(right, bg=config.COLOR_BG_MID, height=40)
        input_frame.pack(fill=tk.X, padx=5, pady=10)
        input_frame.columnconfigure(0, weight=1)

        self.message_box = tk.Text(
            input_frame,
            height=1,
            bg=config.COLOR_BG_MID,
            font=config.FONT_MSG,
            foreground=config.COLOR_TEXT_WHITE,
            wrap=tk.WORD,
        )
        self.message_box.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.message_box.bind("<Return>", self._on_send_message)

        CTkButton(
            master=input_frame,
            text="Enviar",
            width=80,
            corner_radius=10,
            fg_color=config.COLOR_ACCENT,
            text_color=config.COLOR_TEXT_WHITE,
            hover_color=config.COLOR_ACCENT_HOVER,
            command=self._send_message_thread,
        ).grid(row=0, column=1, padx=5, pady=5)

        CTkButton(
            master=input_frame,
            text="Enviar Imagen",
            width=150,
            corner_radius=10,
            fg_color=config.COLOR_ACCENT,
            text_color=config.COLOR_TEXT_WHITE,
            hover_color=config.COLOR_ACCENT_HOVER,
            command=self._send_image,
        ).grid(row=0, column=2, padx=5, pady=5)

    # ------------------------------------------------------------------
    # Handlers de eventos de usuario
    # ------------------------------------------------------------------

    def _on_send_message(self, event=None):
        """Handler de <Return>: envía el mensaje y evita que se inserte salto de línea."""
        if self.message_box.get("1.0", "end-1c"):
            self._send_message_thread()
        return "break"

    def _send_message_thread(self):
        """Lanza el envío en un hilo para no bloquear la GUI."""
        text = self.message_box.get("1.0", "end-1c")
        if not text:
            return
        self.add_message(f"Tú: {text}", "self")
        self.message_box.delete("1.0", tk.END)
        threading.Thread(target=self._net.send_message, args=(text,), daemon=True).start()

    def _send_image(self):
        """Abre el diálogo de archivo, envía la imagen y la muestra localmente."""
        path = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.gif")],
        )
        if not path:
            return
        self.add_message("Tú enviaste una imagen: ◙", "self")
        # Envío en hilo aparte para no congelar la UI durante la transferencia
        threading.Thread(target=self._net.send_image, args=(path,), daemon=True).start()
        self.show_image(path, "enviada")

    def _on_closing(self, win: tk.Toplevel):
        """Confirma el cierre, notifica a los peers y termina el proceso."""
        if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
            self._net.notify_logout()
            self._login_win.destroy()
            win.destroy()
            sys.exit(0)

    # ------------------------------------------------------------------
    # Callbacks de red → UI (llamados desde ChatNetwork)
    # ------------------------------------------------------------------

    def add_message(self, message: str, tag: str):
        """Agrega una línea de texto al área de chat con el estilo del tag dado."""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, message + "\n", tag)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.yview(tk.END)

    def refresh_peer_list(self):
        """Actualiza la lista visual de peers conectados en la barra lateral."""
        self.peers_listbox.delete(0, tk.END)
        for peer in self._net.peers:
            self.peers_listbox.insert(tk.END, f"  ▲ {peer[2]}#{peer[1]}")

    def show_image(self, filepath: str, label: str = "recibida"):
        """Muestra una imagen en una ventana emergente independiente."""
        win = tk.Toplevel()
        win.title(f"Imagen - {label}")
        img = Image.open(filepath)
        img_tk = ImageTk.PhotoImage(img)
        lbl = tk.Label(win, image=img_tk)
        # Mantener referencia al objeto para que el GC no lo elimine
        lbl.image = img_tk
        lbl.pack()
        w, h = max(200, img.width), max(200, img.height)
        win.minsize(200, 200)
        win.geometry(f"{w}x{h}")
