import socket
import threading
from tkinter import scrolledtext
import env
import tkinter as tk
from customtkinter import *
from tkinter import messagebox
import random


class ChatApp:
    def __init__(self):
        self.host = "localhost"  # Host local
        self.port = random.randint(5000, 9999)  # Puerto del usuario
        self.name = None  # Nombre del usuario
        self.peers = []  # Lista de peers
        self.connections = []  # Conexiones con los peers
        self.server_socket = None  # Socket para conexión con el servidor
        self.login = None

        if self.conectar_servidor():  # Verficar conexion con servidor de registro
            self.login_gui()  # Cargar gui

    """1"""

    # Método para conectar al servidor de registro
    def conectar_servidor(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((env.HOST, env.PORT))
            return True
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al conectarse con el servidor: {str(e)}"
            )
            return False

    """2"""

    # Registrar el nodo en el server
    def registrar_nodo(self, username_entry):
        self.name = username_entry.get()  # obtener el texto del textbox

        if not self.name:
            return messagebox.showerror(
                "Error", "El nombre de usuario no puede quedar vacio"
            )

        try:
            self.server_socket.send(
                f"{self.host},{self.port},{self.name}".encode("utf-8")
            )  # Enviar info del nodo

            data = self.server_socket.recv(1024).decode(
                "utf-8"
            )  # Recibir lista de peers
            self.peers = eval(data)  # Actualizar lista de peers
            """AUN PUEDE CAMBIAR A CERRAR LA CONEXION"""

            messagebox.showinfo(
                "¡Bienvenido!",
                "Tu registro ha sido exitoso. ¡Nos alegra tenerte con nosotros!",
            )
            """Cargar GUI del chat"""
            self.login.withdraw()
            self.chat_gui()

        except Exception as e:
            messagebox.showerror("Error", "Eror al enviar datos al servidor")
            return False

    """3"""

    # Método para conectar a otros peers
    def conectar_a_peers(self):
        for peer in self.peers:
            if self.port != peer[1]:  # Evitar conectarse a sí mismo
                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((peer[0], peer[1]))  # Conectar con el peer
                    self.connections.append(client)
                    threading.Thread(
                        target=self.manejador_peer, args=(client, (peer[0], peer[1]))
                    ).start()
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Error al conectar con el peer {peer}: {e}"
                    )

    # Hilo para enviar mensajes
    def hilo_de_mensajes(self):
        mensaje = self.caja_mensaje.get("1.0", "end-1c")
        # Verificar que el mensaje no esta vacio e iniciar el hilo
        if mensaje:
            threading.Thread(target=self.enviar_mensaje).start()

    # Enviar mensajes a todos los peers conectados
    def enviar_mensaje(self):
        mensaje = self.caja_mensaje.get("1.0", "end-1c")
        self.agregar_mensaje(f"Tú: {mensaje}", "self")
        # Enviar el mensaje a todos los peers conectados
        for conn in self.connections:
            try:
                conn.send(f"{self.name}: {mensaje}".encode("utf-8"))
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar el mensaje {e}")

    # Manejar los mensajes entrantes de un peer
    def manejador_peer(self, conn, addr):
        while True:
            try:
                message = conn.recv(1024)
                if not message:
                    break
                self.agregar_mensaje(f"{addr}: {message}", "peer")
            except:
                break
        conn.close()

    # Iniciar el servidor para aceptar conexiones entrantes
    def iniciar_nodo_servidor(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()
        """print(f"Escuchando conexiones entrantes en {self.host}:{self.port}")"""
        while True:
            conn, addr = server.accept()
            self.connections.append(conn)  # Guardar la nueva conexión
            threading.Thread(target=self.manejador_peer, args=(conn, addr)).start()

    def login_gui(self):
        # Configurar la ventana principal
        self.login = tk.Tk()
        self.login.geometry("325x350")
        self.login.title("Chat")
        self.login.configure(bg="#1E1E1E")
        self.login.resizable(False, False)

        # Icono del programa
        icono = tk.PhotoImage(file="images/logo.png")
        self.login.iconphoto(True, icono)

        # Configuración de filas y columnas
        self.login.columnconfigure(0, weight=1)
        self.login.rowconfigure(0, weight=15)
        self.login.rowconfigure(1, weight=15)
        self.login.rowconfigure(2, weight=8)
        self.login.rowconfigure(3, weight=5)

        # Parte del logo
        image = tk.PhotoImage(file="images/logo.png", master=self.login)
        image_label = tk.Label(self.login, image=image, bg="#1E1E1E")
        image_label.grid(row=0, column=0)

        # Nombre de la self.login
        canvas = tk.Canvas(self.login, bg="#1E1E1E", height=20, highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew")
        canvas.create_line(25, 0, 300, 0, fill="#FFFFFF", width=1)
        canvas.create_text(
            162.5, 30, text="CHAT", fill="#FFFFFF", font=("Typo Round Regular Demo", 12)
        )
        canvas.create_line(25, 52, 300, 52, fill="#FFFFFF", width=1)

        # Etiqueta y entrada de texto
        label = tk.Label(
            self.login,
            text="Ingrese su nombre de usuario",
            background="#1E1E1E",
            foreground="white",
            font=("Typo Round Regular Demo", 12),
            justify="center",
        )
        label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=25, pady=(0, 80))

        username = CTkEntry(master=self.login, height=24, width=275, corner_radius=5)
        username.grid(row=2, column=0, sticky="we", padx=25, pady=(0, 0))

        # Botón para ingresar
        btn = CTkButton(
            text="Ingresar",
            width=275,
            corner_radius=10,
            fg_color="#29BCF6",
            text_color="#FFFFFF",
            hover_color="#86E8B5",
            command=lambda: self.registrar_nodo(username_entry=username),
        )
        btn.grid(row=3, column=0, columnspan=2, sticky="we", padx=25, pady=(0, 30))

        # Ejecutar la aplicación
        self.login.mainloop()

    def agregar_mensaje(self, mensaje, tag):
        # Crear frame temporal para el mensaje
        bubble_frame = tk.Frame(self.chat_canvas, bg="#434343", pady=5)

        # Configurar colores y alineación para cada tipo de mensaje
        if tag == "peer":
            color_fondo = "#00FF00"  # Verde para peers
            justificacion = "w"  # Alineado a la izquierda
            anchor_pos = "nw"
        else:
            color_fondo = "#00BFFF"  # Azul para tus mensajes
            justificacion = "e"  # Alineado a la derecha
            anchor_pos = "ne"

        # Crear la "burbuja" del mensaje
        mensaje_label = tk.Label(
            bubble_frame,
            text=mensaje,
            bg=color_fondo,
            fg="white",
            font=("Segoe UI", 12),
            wraplength=500,  # Ajusta este valor según el tamaño de la burbuja
            padx=10,
            pady=5,
        )

        # Posicionar la burbuja en la ventana de chat
        mensaje_label.pack(
            side=tk.LEFT if tag == "peer" else tk.RIGHT, anchor=justificacion, padx=10
        )

        # Crear la ventana en el canvas con la burbuja alineada
        self.chat_canvas.create_window(
            (
                5 if tag == "peer" else self.chat_canvas.winfo_width() - 5
            ),  # Alinear a izquierda o derecha
            self.y_position,
            anchor=anchor_pos,
            window=bubble_frame,
        )

        # Ajustar la posición vertical para el próximo mensaje
        self.y_position += bubble_frame.winfo_reqheight() + 10

        # Desplazar el scroll hacia el final
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def chat_gui(self):
        app = tk.Toplevel()  # Cambiar de Toplevel a Tk para crear la ventana principal

        # Evento al cerrar la ventana
        def on_closing():
            if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
                app.destroy()
                self.login.deiconify()

        app.geometry("1000x700")
        app.title("CHAT")
        app.configure(bg="#1E1E1E")
        app.minsize(800, 600)

        main_frame = tk.Frame(app)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Barra lateral de contactos
        barra_contactos = tk.Frame(main_frame, bg="#1E1E1E", width=200)
        barra_contactos.pack(side=tk.LEFT, fill=tk.Y)

        lbl_nombreUsuario = tk.Label(
            barra_contactos,
            text=self.name,
            font=("Segoe UI", 20),
            justify="left",
            foreground="white",
            background="#1E1E1E",
        )
        lbl_nombreUsuario.pack(fill=tk.X, padx=50, pady=5)

        # --- Sección del chat ---
        right_frame = tk.Frame(main_frame, bg="#737373")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Canvas para los mensajes
        self.chat_canvas = tk.Canvas(right_frame, bg="#434343")
        self.chat_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar para el Canvas
        scrollbar = tk.Scrollbar(right_frame, command=self.chat_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.config(yscrollcommand=scrollbar.set)

        # Frame interior para contener los mensajes
        self.chat_frame = tk.Frame(self.chat_canvas, bg="#434343")
        self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")

        # Atributo para mantener la posición vertical
        self.y_position = 0

        # --- Sección de envío de mensajes ---
        mensaje_frame = tk.Frame(right_frame, bg="#434343", height=40)
        mensaje_frame.pack(fill=tk.X, padx=5, pady=10)

        # Caja de entrada de mensajes
        self.caja_mensaje = tk.Text(
            mensaje_frame,
            height=1,
            width=60,
            bg="#434343",
            font=("Segoe UI", 15),
            foreground="#FFFFFF",
            wrap=tk.WORD,
        )
        self.caja_mensaje.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Botón de enviar mensaje
        btn = CTkButton(
            master=mensaje_frame,
            text="Enviar",
            width=100,
            corner_radius=10,
            fg_color="#29BCF6",
            text_color="#FFFFFF",
            hover_color="#86E8B5",
            command=self.hilo_de_mensajes,
        )
        btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        # Verificar si se va a cerrar la ventana
        app.protocol("WM_DELETE_WINDOW", on_closing)

        # Cargar backend
        self.conectar_a_peers()

        # Hilo para iniciar el nodo como servidor
        threading.Thread(target=self.iniciar_nodo_servidor).start()

        # Ejecutar la aplicación
        app.mainloop()


if __name__ == "__main__":
    ChatApp()
