from tkinter import messagebox, filedialog
from tkinter import Image, scrolledtext
from cryptography.fernet import Fernet
from PIL import Image, ImageTk
from customtkinter import *
import tkinter as tk
import threading
import random
import socket
import errno
import env
import os

class ChatApp:
    def __init__(self):
        
        #Variables de conexion
        hostname = socket.gethostname()
        self.host = socket.gethostbyname(hostname)  # Dirección IP
        self.port = random.randint(5000, 9999)  # Puerto generado aleatoriamente
        self.server_socket = None  # Socket del servidor de registro
        
        #Variables de almacenamiento
        self.connections = []  # Conexiones con otros peers
        self.peers = []  # Lista de peers conectados
        self.peer_info = None  # Información de peer
        self.name = None  # Nombre del usuario
        
        #Encriptacion
        self.cipher_suite = Fernet(env.KEY)
        
        #Variable de front
        self.login = None  # Ventana de login

        # Si se puede conectar al servidor de registro, mostrar la ventana de login
        if self.conectar_servidor():
            self.login_gui()

    """Backend"""

    def encrypt_data(self,data):
    # Encriptar los datos
        return self.cipher_suite.encrypt(data.encode())
    
    def decrypt_data(self,encrypted_data):
    # Desencriptar los datos
        return self.cipher_suite.decrypt(encrypted_data).decode()
    
    def conectar_servidor(self): #Funcion para contectarse al servidor
        """Intenta conectarse al servidor de registro."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((env.HOST, env.PORT))  # Conecta al servidor
            return True
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al conectarse con el servidor: {str(e)}"
            )
            return False
    
    def iniciar_nodo_servidor(self):
        """Inicia el nodo como servidor para aceptar conexiones de peers."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port)) #Acepta conexiones en su ip y puerto
        server.listen() #Se mantiene escuchando
        while True:
            conn, addr = server.accept() #Acepta cualquier conexion
            self.connections.append(conn) #Agrega a la lista de conexiones la informacion del peer conectado
            threading.Thread(target=self.manejador_peer, args=(conn, addr)).start() #Inicia un nuevo hilo para manejar un cliente
    
    def registrar_nodo(self, username_entry): #Registra el nodo en el servidor 
        """Registra el usuario en el servidor y actualiza la lista de peers."""
        self.name = username_entry.get()  # Obtener el nombre de usuario
        if not self.name:
            return messagebox.showerror(
                "Error", "El nombre de usuario no puede quedar vacío"
            )

        try:
            #Enviar los datos de registro al servidor
            #Crear mensaje y encriptarlo
            register_message = f"[REGISTER],{self.host},{self.port},{self.name}"
            encrypted_message = self.encrypt_data(register_message)
            
            #Enviar mensaje encriptado
            self.server_socket.send(encrypted_message)
            
            # Recibir lista de peers (encriptada)
            encrypted_data = self.server_socket.recv(1024)  
            
            # Desencriptar la respuesta
            data = self.decrypt_data(encrypted_data)  
            
            self.peers = eval(data)  # Convertir la lista de peers a formato Python
            
            messagebox.showinfo("¡Bienvenido!", "Tu registro ha sido exitoso.") #Mensaje de retroalimentacion
            
            self.login.withdraw()  # Cerrar ventana de login
            
            self.chat_gui()  # Abrir ventana de chat
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar datos al servidor {e}")
            return False
    
    def enviar_notificacion_usuario(self, command):
        """Notifica a los peers cuando un usuario se une o se desconecta."""
        if command == "LOGIN":
            #Encripta el mensaje de notificacion
            notification_message = f"{self.host}#{self.name}#{self.port} se ha unido al chat."
            encrypted_message = self.encrypt_data(notification_message)
            
            for conn in self.connections: 
                try:
                    conn.send(encrypted_message) #Envia a todos los peers conectados el mensaje
                except socket.error as e:
                    if e.errno == errno.WSAENOTSOCK:  # Error de socket
                        conn.close()
                except Exception as e:
                    conn.close()
            self.agregar_mensaje("Te has unido al chat", "new_user") #Mensaje de retroalimentacion para si mismo
        else:
            desconection_message = f"{self.name}#{self.port} ha salido del chat." #Mensaje de desconexion
            encrypted_message = self.encrypt_data(desconection_message) #encriptar mensaje
            for conn in self.connections:
                try:
                    conn.send(encrypted_message) #enviar a todos
                except Exception as e:
                    conn.close()

    def conectar_a_peers(self):
        """Conectar con los peers registrados."""
        for peer in self.peers:
            if self.port != peer[1]:  # Evitar conectarse a si mismo
                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((peer[0], peer[1]))  # Conectar con el peer
                    self.connections.append(client)  # Añadir a la lista de conexiones
                    # Iniciar un hilo para manejar la comunicación con el peer
                    threading.Thread(target=self.manejador_peer, args=(client, (peer[0], peer[1]))).start()
                except Exception as e:
                    client.close()
        self.enviar_notificacion_usuario(command="LOGIN")  # Notificar a los peers

    def hilo_de_mensajes(self):
        """Inicia un nuevo hilo para enviar un mensaje."""
        mensaje = self.caja_mensaje.get("1.0", "end-1c")
        if mensaje:
            threading.Thread(target=self.enviar_mensaje).start()
    
    def manejador_peer(self, conn, addr): #Manejador de peer para todas las operaciones a realizar
        """Maneja la comunicación con un peer."""
        while True:
            try:
                encrypted_message = conn.recv(1024) #Recibir imagen o mensaje encriptado
                
                if not encrypted_message:
                    break
                
                message = self.decrypt_data(encrypted_message) #Desencriptar el mensaje
                
                if message.startswith("IMG:"):  # Si es una imagen
                    _, filename, filesize = message.split(":")
                    filesize = int(filesize)

                    # Guardar la imagen
                    with open(f"received_{filename}", "wb") as img_file:
                        bytes_received = 0
                        while bytes_received < filesize:
                            img_data = conn.recv(1024)
                            img_file.write(img_data)
                            bytes_received += len(img_data)
                    
                    
                    # Construir la ruta completa del archivo
                    filepath = f"received_{filename}"

                    # Agregar un mensaje indicando que se recibió una imagen
                    self.agregar_mensaje(f"{addr}: Envió una imagen: ◙", "peer")

                    # Mostrar la imagen usando el filepath
                    self.mostrar_imagen(filepath,"recibida")

                elif "ha salido del chat" in message:  # Manejo de desconexión de un peer
                    parts = message.split("#")
                    port = "".join(filter(str.isdigit, parts[1]))
                    port = int(port)
                    self.peers = [peer for peer in self.peers if peer[1] != port] #Remueve de la lista visualmente
                    self.eliminar_conexion(port) #Remueve de la lista logicamente
                    self.actualizar_lista_peers() #Actualiza la vista de los peers conectados
                    self.agregar_mensaje(f"{message}", "leave") #Manda mensaje a todos 
                else:
                    ip, usuario, port = message.split("#")
                    port = int(port[:4])  # Corregir el puerto
                    self.peer_info = (ip, port, usuario) 
                    if self.peer_info not in self.peers: #Agrega un nuevo peer a la lista visual si no esta 
                        self.peers.append(self.peer_info)
                        self.actualizar_lista_peers() #Actualiza la vista de los peers conectados
                    partes = message.split("#", 1)
                    message = partes[1] if len(partes) > 1 else message #Formatea el mensaje
                    self.agregar_mensaje(f"{message}", "peer") #Envia mensaje a todos
            except Exception as e:
                pass
        conn.close()

    def eliminar_conexion(self, puerto):
        """Elimina una conexión con un peer desconectado."""
        for client in self.connections:
            try:
                _, client_port = client.getpeername()  # Obtener puerto del peer
                if client_port == puerto:
                    client.close() #Cierra la conexion con ese cliente
                    self.connections.remove(client) #Se remueve de la lista de conexiones
                    break
            except Exception: 
                pass #Omitimos para no generar errores de mandar mensaje a un peer que no esta
    
    def actualizar_lista_peers(self): #Actualiza la lista de peers conectados en el front
        """Actualiza la lista gráfica de peers en el chat."""
        self.peers_listbox.delete(0, tk.END)  # Limpia la lista actual
        for peer in self.peers:
            self.peers_listbox.insert(
                tk.END, f"  ▲ {peer[2]}#{peer[1]}"
            )  # Insertar nuevo peer

    def enviar_mensaje(self):
        """Envía un mensaje a todos los peers conectados."""
        txt_mensaje = self.caja_mensaje.get("1.0", "end-1c")
        self.agregar_mensaje(f"Tú: {txt_mensaje}", "self")
        
        message = f"{self.host}#{self.name}#{self.port}: {txt_mensaje}" #Armar el mensaje
        encrypted_message = self.encrypt_data(message)
             
        for conn in self.connections:
            try:
                conn.send(encrypted_message)
            except socket.error as e:
                if e.errno == errno.WSAENOTSOCK:  # Error de socket
                    conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar el mensaje {e}")
        self.caja_mensaje.delete("1.0", tk.END)
    
    def enviar_imagen(self):
        """Selecciona y envía una imagen a los peers."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.gif")],
        )
        if not file_path:
            return

        self.agregar_mensaje(f"Tú enviaste una imagen: ◙", "self")

        for conn in self.connections:
            try:
                # Obtener metadatos del archivo (sin encriptar)
                filename = os.path.basename(file_path)
                filesize = os.path.getsize(file_path)

                # Enviar los metadatos del archivo (nombre y tamaño)
                message = f"IMG:{filename}:{filesize}"
                encrypted_message = self.encrypt_data(message)  # Cifrar metadatos
                conn.sendall(encrypted_message)  # Enviar metadatos cifrados

                with open(file_path, "rb") as img_file:
                    img_data = img_file.read(1024)
                    while img_data:
                        conn.send(img_data)
                        img_data = img_file.read(1024)
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar la imagen: {e}")
            # Función para mostrar la imagen en una nueva ventana
            self.mostrar_imagen(file_path,"enviada")

        
    def mostrar_imagen(self, ruta, command):
        # Crear una nueva ventana
        ventana_imagen = tk.Toplevel()
        ventana_imagen.title(f"Imagen-{command}")

        # Abrir la imagen usando PIL
        imagen = Image.open(ruta)
        imagen_tk = ImageTk.PhotoImage(imagen)

        # Crear un label para mostrar la imagen
        label_imagen = tk.Label(ventana_imagen, image=imagen_tk)
        label_imagen.image = imagen_tk  # Necesario para evitar que la imagen se recolecte como basura
        label_imagen.pack()

        # Ajustar el tamaño de la ventana al tamaño de la imagen
        ventana_imagen.geometry(f"{imagen.width}x{imagen.height}")  # Establecer tamaño inicial

        # Establecer el tamaño mínimo de la ventana
        ventana_imagen.minsize(200, 200)

        # Ajustar el tamaño de la ventana después de que la imagen se haya cargado
        ventana_imagen.update_idletasks()  # Asegúrate de que se actualicen los cambios en la ventana
        ventana_imagen.geometry(f"{max(200, imagen.width)}x{max(200, imagen.height)}")  # Asegurarse de que sea al menos 200x200


    """Front"""
    
    def agregar_mensaje(self, mensaje, tag):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, mensaje + "\n", tag)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.yview(tk.END)
    
    def login_gui(self):
        def evento_enviar_usuario(event= None):
            self.registrar_nodo(username_entry=self.username)
            return "break"  # Evita que el evento Enter añada una nueva línea
            
        self.login = tk.Tk()
        self.login.title("Chat")
        self.login.configure(bg="#1E1E1E")
        self.login.resizable(False, False)

        # Obtener el tamaño de la pantalla
        ancho_pantalla = self.login.winfo_screenwidth()
        alto_pantalla = self.login.winfo_screenheight()
        
        # Calcular la posición para centrar la ventana
        pos_x = int((ancho_pantalla / 2) - (325 / 2))
        pos_y = int((alto_pantalla / 2) - (350 / 2))
        
        # Establecer la geometría de la ventana (tamaño y posición)
        self.login.geometry(f"{325}x{350}+{pos_x}+{pos_y}")
        
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
        username.bind("<Return>",evento_enviar_usuario)

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

    def chat_gui(self):
        app = tk.Toplevel()

        def on_closing():
            if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
                self.enviar_notificacion_usuario(command="LOGOUT")
                self.login.destroy()
                app.destroy()
                sys.exit(0)
        def evento_enviar_mensaje(event): #Evento para utilizar el enter
            mensaje = self.caja_mensaje.get("1.0", "end-1c")
            if mensaje:
                self.enviar_mensaje()
            return "break"  # Evita que el evento Enter añada una nueva línea
        
        # Crear la ventana del chat
        app.title(f"CHAT - {self.name.upper()}#{self.port}")
        app.configure(bg="#1E1E1E")

        # Obtener el tamaño de la pantalla
        ancho_pantalla = app.winfo_screenwidth()
        alto_pantalla = app.winfo_screenheight()  # Asegúrate de usar 'app' en lugar de 'self.chat_gui'

        # Calcular la posición para centrar la ventana
        pos_x = int((ancho_pantalla / 2) - (1000 / 2))
        pos_y = int((alto_pantalla / 2) - (700 / 2))

        # Establecer la geometría de la ventana (tamaño y posición)
        app.geometry(f"1000x700+{pos_x}+{pos_y}")
        
        app.minsize(800,650)
                
        icono = tk.PhotoImage(file="images/logo.png")
        app.iconphoto(True, icono)

        main_frame = tk.Frame(app)
        main_frame.pack(fill=tk.BOTH, expand=True)

        barra_contactos = tk.Frame(main_frame, bg="#1E1E1E", width=200)
        barra_contactos.pack(side=tk.LEFT, fill=tk.Y)

        lbl_nombreUsuario = tk.Label(
            barra_contactos,
            text=f"!Hola {self.name}!",
            font=("Segoe UI", 20),
            justify="left",
            foreground="#7d3c98",
            background="#1E1E1E",
        )
        lbl_nombreUsuario.pack(fill=tk.X, padx=50, pady=5)

        lbl_peersConectados = tk.Label(
            barra_contactos,
            text="● Usuarios conectados",
            font=("Segoe UI", 16),
            justify="left",
            foreground="#2ecc71",
            background="#1E1E1E",
            
        )
        lbl_peersConectados.pack(fill=tk.X, padx=0, pady=5)

        self.peers_listbox = tk.Listbox(
            barra_contactos,
            bg="#1E1E1E",
            fg="#82e0aa",
            font=("Segoe UI", 12),
            selectbackground="#434343",
            bd=0,
        )
        self.peers_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.actualizar_lista_peers()
        
        # Cambiar el color del borde resaltado
        self.peers_listbox.configure(highlightbackground="#737373", highlightcolor="#82e0aa")  # Cambia a tus colores deseados
        self.actualizar_lista_peers()
        
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
        self.chat_text.tag_configure("new_user", foreground="#f1c40f")
        self.chat_text.tag_configure("leave", foreground="#e74c3c")

        self.caja_mensaje = tk.Text(
            mensaje_frame,
            height=1,
            bg="#434343",
            font=("Segoe UI", 15),
            foreground="#FFFFFF",
            wrap=tk.WORD,
        )
        self.caja_mensaje.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.caja_mensaje.bind("<Return>", evento_enviar_mensaje)

        btn_send = CTkButton(
            master=mensaje_frame,
            text="Enviar",
            width=80,
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
            width=150,
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
