import socket
import threading
from tkinter import scrolledtext
import env
import tkinter as tk
from customtkinter import *
from tkinter import messagebox, filedialog
import random
import os


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

    def enviar_notificacion_nuevo_usuario(self):
        """Envía una notificación a todos los peers de que un nuevo usuario se ha unido."""
        mensaje = f"{self.name}#{self.port} se ha unido al chat."
        for conn in self.connections:
            try:
                conn.send(mensaje.encode("utf-8"))
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar la notificación: {e}")
        self.agregar_mensaje("Te has unido al chat", "peer")

    def registrar_nodo(self, username_entry):
        self.name = username_entry.get()  # obtener el texto del textbox

        if not self.name:
            return messagebox.showerror(
                "Error", "El nombre de usuario no puede quedar vacio"
            )

        try:
            self.server_socket.send(
                f"[REGISTER],{self.host},{self.port},{self.name}".encode("utf-8")
            )
            data = self.server_socket.recv(1024).decode("utf-8")
            self.peers = eval(data)  # Actualizar lista de peers

            messagebox.showinfo(
                "¡Bienvenido!",
                "Tu registro ha sido exitoso. ¡Nos alegra tenerte con nosotros!",
            )
            self.login.withdraw()
            self.chat_gui()

        except Exception as e:
            messagebox.showerror("Error", "Error al enviar datos al servidor")
            return False

    def conectar_a_peers(self):
        for peer in self.peers:
            if self.port != peer[1]:  # Evitar conectarse a sí mismo
                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((peer[0], peer[1]))  # Conectar con el peer
                    self.connections.append(client)
                    # Enviar notificación a todos los peers de que un nuevo usuario se ha unido

                    threading.Thread(
                        target=self.manejador_peer, args=(client, (peer[0], peer[1]))
                    ).start()
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Error al conectar con el peer {peer}: {e}"
                    )
        self.enviar_notificacion_nuevo_usuario()

    def hilo_de_mensajes(self):
        mensaje = self.caja_mensaje.get("1.0", "end-1c")
        if mensaje:
            threading.Thread(target=self.enviar_mensaje).start()

    def enviar_mensaje(self):
        mensaje = self.caja_mensaje.get("1.0", "end-1c")
        self.agregar_mensaje(f"Tú: {mensaje}", "self")
        for conn in self.connections:
            try:
                conn.send(f"{self.name}: {mensaje}".encode("utf-8"))
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar el mensaje {e}")

    def enviar_imagen(self):
        # Abrir un cuadro de diálogo para seleccionar una imagen
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[("Imagenes", "*.png;*.jpg;*.jpeg;*.gif")],
        )
        if not file_path:
            return

        self.agregar_mensaje(
            f"Tú enviaste una imagen: {os.path.basename(file_path)}", "self"
        )

        for conn in self.connections:
            try:
                # Enviar la longitud del nombre del archivo
                filename = os.path.basename(file_path)
                conn.send(
                    f"IMG:{filename}:{os.path.getsize(file_path)}".encode("utf-8")
                )

                # Enviar la imagen en chunks
                with open(file_path, "rb") as img_file:
                    img_data = img_file.read(1024)  # Leer en bloques de 1024 bytes
                    while img_data:
                        conn.send(img_data)
                        img_data = img_file.read(1024)
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar la imagen: {e}")

    def manejador_peer(self, conn, addr):
        while True:
            try:
                # Recibir el mensaje
                message = conn.recv(1024)
                if not message:
                    break

                # Verificar si es una imagen
                message_str = message.decode("utf-8")
                if message_str.startswith("IMG:"):
                    # Si es un mensaje de imagen
                    _, filename, filesize = message_str.split(":")
                    filesize = int(filesize)

                    # Recibir la imagen
                    with open(f"received_{filename}", "wb") as img_file:
                        bytes_received = 0
                        while bytes_received < filesize:
                            img_data = conn.recv(1024)
                            img_file.write(img_data)
                            bytes_received += len(img_data)

                    self.agregar_mensaje(
                        f"{addr}: Enviaron una imagen: {filename}", "peer"
                    )
                else:
                    # Aquí es donde manejamos el mensaje normal (incluyendo la notificación)
                    self.agregar_mensaje(f"{message_str}", "peer")
            except:
                break
        conn.close()

    def iniciar_nodo_servidor(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()
        while True:
            conn, addr = server.accept()
            self.connections.append(conn)  # Guardar la nueva conexión
            threading.Thread(target=self.manejador_peer, args=(conn, addr)).start()

    def login_gui(self):
        self.login = tk.Tk()
        self.login.geometry("325x350")
        self.login.title("Chat")
        self.login.configure(bg="#1E1E1E")
        self.login.resizable(False, False)

        icono = tk.PhotoImage(file="images/logo.png")
        self.login.iconphoto(True, icono)

        self.login.columnconfigure(0, weight=1)
        self.login.rowconfigure(0, weight=15)
        self.login.rowconfigure(1, weight=15)
        self.login.rowconfigure(2, weight=8)
        self.login.rowconfigure(3, weight=5)

        image = tk.PhotoImage(file="images/logo.png", master=self.login)
        image_label = tk.Label(self.login, image=image, bg="#1E1E1E")
        image_label.grid(row=0, column=0)

        canvas = tk.Canvas(self.login, bg="#1E1E1E", height=20, highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew")
        canvas.create_line(25, 0, 300, 0, fill="#FFFFFF", width=1)
        canvas.create_text(
            162.5, 30, text="CHAT", fill="#FFFFFF", font=("Typo Round Regular Demo", 12)
        )
        canvas.create_line(25, 52, 300, 52, fill="#FFFFFF", width=1)

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

        self.login.mainloop()

    def agregar_mensaje(self, mensaje, tag):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, mensaje + "\n", tag)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.yview(tk.END)

    def chat_gui(self):
        app = tk.Toplevel()

        def on_closing():
            if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
                app.destroy()
                self.login.deiconify()

        app.geometry("1000x700")
        app.title("CHAT")
        app.configure(bg="#1E1E1E")

        icono = tk.PhotoImage(file="images/logo.png")
        app.iconphoto(True, icono)

        main_frame = tk.Frame(app)
        main_frame.pack(fill=tk.BOTH, expand=True)

        barra_contactos = tk.Frame(main_frame, bg="#1E1E1E", width=200)
        barra_contactos.pack(side=tk.LEFT, fill=tk.Y)

        lbl_nombreUsuario = tk.Label(
            barra_contactos,
            text="Usuario: " + self.name,
            font=("Segoe UI", 20),
            justify="left",
            foreground="white",
            background="#1E1E1E",
        )
        lbl_nombreUsuario.pack(fill=tk.X, padx=50, pady=5)

        lbl_peersConectados = tk.Label(
            barra_contactos,
            text="Usuarios conectados",
            font=("Segoe UI", 16),
            justify="right",
            foreground="white",
            background="#1E1E1E",
        )
        lbl_peersConectados.pack(fill=tk.X, padx=10, pady=5)

        self.peers_listbox = tk.Listbox(
            barra_contactos,
            bg="#1E1E1E",
            fg="white",
            font=("Segoe UI", 12),
            selectbackground="#434343",
        )
        self.peers_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        for peer in self.peers:
            self.peers_listbox.insert(tk.END, f"●{peer[2]}#{peer[1]})")

        right_frame = tk.Frame(main_frame, bg="#737373")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        barra_superior = tk.Frame(right_frame, bg="#434343", height=60)
        barra_superior.pack(fill=tk.X)

        self.chat_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#434343",
            font=("Segoe UI", 12),
            foreground="#FFFFFF",
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        mensaje_frame = tk.Frame(right_frame, bg="#434343", height=40)
        mensaje_frame.pack(fill=tk.X, padx=5, pady=10)

        mensaje_frame.columnconfigure(0, weight=1)
        mensaje_frame.columnconfigure(1, weight=0)
        mensaje_frame.columnconfigure(2, weight=0)

        self.chat_text.tag_configure("peer", foreground="#00FF00")
        self.chat_text.tag_configure("self", foreground="#00BFFF", justify="right")

        self.caja_mensaje = tk.Text(
            mensaje_frame,
            height=1,
            bg="#434343",
            font=("Segoe UI", 15),
            foreground="#FFFFFF",
            wrap=tk.WORD,
        )
        self.caja_mensaje.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        btn_send = CTkButton(
            master=mensaje_frame,
            text="Enviar",
            width=100,
            corner_radius=10,
            fg_color="#29BCF6",
            text_color="#FFFFFF",
            hover_color="#86E8B5",
            command=self.hilo_de_mensajes,
        )
        btn_send.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        # Botón para enviar imágenes
        btn_send_image = CTkButton(
            master=mensaje_frame,
            text="Enviar Imagen",
            width=100,
            corner_radius=10,
            fg_color="#29BCF6",
            text_color="#FFFFFF",
            hover_color="#86E8B5",
            command=self.enviar_imagen,
        )
        btn_send_image.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        app.protocol("WM_DELETE_WINDOW", on_closing)

        self.conectar_a_peers()
        threading.Thread(target=self.iniciar_nodo_servidor).start()

        app.mainloop()


if __name__ == "__main__":
    ChatApp()
