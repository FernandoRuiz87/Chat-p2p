"""
Módulo de red P2P.

Gestiona toda la comunicación de sockets: conexión al servidor de registro,
aceptación de peers entrantes, envío y recepción de mensajes e imágenes.

Los eventos que afectan a la UI se notifican mediante callbacks que la capa
de presentación (ChatGUI) registra antes de iniciar la sesión.
"""

import errno
import json
import os
import random
import socket
import threading
from typing import Callable, List, Optional, Tuple

from config import config
import crypto

# Tipo que representa a un peer: (ip, puerto, nombre)
PeerInfo = Tuple[str, int, str]


class ChatNetwork:
    """
    Gestiona toda la lógica de red del nodo P2P.

    Los métodos de red que producen eventos visibles para el usuario
    (nuevo mensaje, cambio en la lista de peers, imagen recibida)
    invocan los callbacks registrados por la GUI.
    """

    def __init__(self):
        hostname = socket.gethostname()
        self.host: str = socket.gethostbyname(hostname)
        self.port: int = random.randint(5000, 9999)
        self.name: str = ""

        self.connections: List[socket.socket] = []
        self.peers: List[PeerInfo] = []

        # Socket de conexión con el servidor de registro
        self._registry_socket: Optional[socket.socket] = None

        # Callbacks registrados por la GUI — se asignan antes de llamar a connect_to_peers()
        self.on_message: Callable[[str, str], None] = lambda msg, tag: None
        self.on_peer_list_changed: Callable[[], None] = lambda: None
        self.on_image_received: Callable[[str], None] = lambda path: None

    # ------------------------------------------------------------------
    # Servidor de registro
    # ------------------------------------------------------------------

    def connect_to_registry(self) -> bool:
        """Establece la conexión TCP con el servidor de registro central."""
        try:
            self._registry_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._registry_socket.connect((config.SERVER_HOST, config.SERVER_PORT))
            return True
        except Exception:
            return False

    def register_node(self, name: str) -> bool:
        """
        Registra este nodo en el servidor de registro.

        Envía ip, puerto y nombre cifrados; recibe la lista de peers
        activos serializada en JSON.

        Returns:
            True si el registro fue exitoso, False en caso contrario.
        """
        self.name = name
        message = f"[REGISTER],{self.host},{self.port},{self.name}"
        try:
            self._registry_socket.send(crypto.encrypt(message))
            encrypted_response = self._registry_socket.recv(1024)
            # JSON convierte tuplas a listas al deserializar, por eso
            # normalizamos cada entrada a tupla para mantener tipos consistentes.
            raw = json.loads(crypto.decrypt(encrypted_response))
            self.peers = [tuple(p) for p in raw]
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Servidor del nodo (acepta conexiones P2P entrantes)
    # ------------------------------------------------------------------

    def start_node_server(self):
        """
        Inicia el servidor TCP de este nodo.
        Debe ejecutarse en un hilo aparte para no bloquear la GUI.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()
        while True:
            conn, addr = server.accept()
            self.connections.append(conn)
            threading.Thread(
                target=self._handle_peer, args=(conn, addr), daemon=True
            ).start()

    # ------------------------------------------------------------------
    # Conexión con peers existentes y notificaciones
    # ------------------------------------------------------------------

    def connect_to_peers(self):
        """
        Conecta con todos los peers de la lista del servidor
        y anuncia la llegada de este nodo al chat.
        """
        for peer in self.peers:
            if self.port == peer[1]:  # Evitar conectarse a sí mismo
                continue
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((peer[0], peer[1]))
                self.connections.append(client)
                threading.Thread(
                    target=self._handle_peer,
                    args=(client, (peer[0], peer[1])),
                    daemon=True,
                ).start()
            except Exception:
                client.close()
        self._broadcast_join()

    def notify_logout(self):
        """
        Notifica la desconexión de este nodo.

        1. Avisa a los peers P2P directamente (via self.connections).
        2. Cierra el socket del servidor de registro para que el servidor
           reciba un FIN limpio, detecte la desconexión y elimine este
           nodo de su lista de peers activos.
        """
        message = f"{self.name}#{self.port} ha salido del chat."
        encrypted = crypto.encrypt(message)
        for conn in self.connections:
            try:
                conn.send(encrypted)
            except Exception:
                conn.close()

        # Cerrar la conexión con el servidor de registro.
        # Sin esto, el servidor queda bloqueado en recv() y nunca detecta
        # que el cliente salió, dejando el peer "fantasma" en la lista.
        if self._registry_socket:
            try:
                self._registry_socket.close()
            except Exception:
                pass
            self._registry_socket = None

    # ------------------------------------------------------------------
    # Envío de mensajes e imágenes
    # ------------------------------------------------------------------

    def send_message(self, text: str):
        """
        Envía un mensaje de texto a todos los peers.
        Formato del protocolo: ip#nombre#puerto: texto
        """
        payload = f"{self.host}#{self.name}#{self.port}: {text}"
        encrypted = crypto.encrypt(payload)
        for conn in self.connections:
            try:
                conn.send(encrypted)
            except socket.error as e:
                if e.errno == errno.WSAENOTSOCK:
                    conn.close()
            except Exception:
                pass

    def send_image(self, file_path: str):
        """
        Envía una imagen a todos los peers.
        Protocolo: primero se envían los metadatos cifrados (IMG:nombre:tamaño),
        luego se transmiten los bytes crudos del archivo en bloques de 1 KB.
        """
        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)
        header = crypto.encrypt(f"IMG:{filename}:{filesize}")
        for conn in self.connections:
            try:
                conn.sendall(header)
                with open(file_path, "rb") as f:
                    chunk = f.read(1024)
                    while chunk:
                        conn.send(chunk)
                        chunk = f.read(1024)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _broadcast_join(self):
        """Anuncia a todos los peers conectados que este nodo se ha unido."""
        message = f"{self.host}#{self.name}#{self.port} se ha unido al chat."
        encrypted = crypto.encrypt(message)
        for conn in self.connections:
            try:
                conn.send(encrypted)
            except socket.error as e:
                if e.errno == errno.WSAENOTSOCK:
                    conn.close()
            except Exception:
                conn.close()
        self.on_message("Te has unido al chat", "new_user")

    def _handle_peer(self, conn: socket.socket, addr):
        """
        Bucle de recepción para un peer específico.
        Clasifica cada mensaje entrante y lo despacha al handler correcto.
        """
        while True:
            try:
                encrypted = conn.recv(1024)
                if not encrypted:
                    break
                message = crypto.decrypt(encrypted)

                if message.startswith("IMG:"):
                    self._receive_image(conn, addr, message)
                elif "ha salido del chat" in message:
                    self._handle_peer_disconnect(message)
                else:
                    self._handle_text_message(message)
            except Exception:
                pass
        conn.close()

    def _receive_image(self, conn: socket.socket, addr, header: str):
        """Recibe los bytes de una imagen a partir del encabezado IMG:nombre:tamaño."""
        _, filename, filesize_str = header.split(":")
        filesize = int(filesize_str)
        filepath = f"received_{filename}"
        with open(filepath, "wb") as f:
            received = 0
            while received < filesize:
                chunk = conn.recv(1024)
                f.write(chunk)
                received += len(chunk)

        # Buscar el nombre del remitente por IP en la lista de peers.
        # No usamos el puerto de addr porque es el puerto efímero del cliente,
        # no el puerto de escucha registrado en self.peers.
        sender_ip = addr[0]
        sender_name = next((p[2] for p in self.peers if p[0] == sender_ip), sender_ip)
        print(sender_name, sender_ip)

        self.on_message(f"{sender_name}#{addr[1]}: Envió una imagen: ◙", "peer")
        self.on_image_received(filepath)


    def _add_peer(self, peer_info: "PeerInfo") -> bool:
        """
        Agrega un peer a la lista si no existe ya (deduplicación por puerto).

        Usar el puerto como clave única evita duplicados incluso si el tipo
        del objeto difiere (ej. tupla vs lista tras deserializar JSON).

        Returns:
            True si el peer fue agregado, False si ya existía.
        """
        if not any(p[1] == peer_info[1] for p in self.peers):
            self.peers.append(peer_info)
            return True
        return False

    def _handle_peer_disconnect(self, message: str):
        """Elimina al peer desconectado de la lista y notifica a la GUI."""
        parts = message.split("#")
        port = int("".join(filter(str.isdigit, parts[1])))
        self.peers = [p for p in self.peers if p[1] != port]
        self._remove_connection(port)
        self.on_peer_list_changed()
        self.on_message(message, "leave")

    def _handle_text_message(self, message: str):
        """Registra al peer si es nuevo y muestra su mensaje en el chat."""
        ip, usuario, port_and_rest = message.split("#")
        port = int(port_and_rest[:4])
        peer_info = (ip, port, usuario)
        # _add_peer() compara por puerto para evitar duplicados
        # independientemente del tipo (tupla vs lista)
        if self._add_peer(peer_info):
            self.on_peer_list_changed()
        _, body = message.split("#", 1)
        self.on_message(body, "peer")

    def _remove_connection(self, port: int):
        """Cierra y elimina del registro la conexión con el peer del puerto dado."""
        for conn in self.connections:
            try:
                _, client_port = conn.getpeername()
                if client_port == port:
                    conn.close()
                    self.connections.remove(conn)
                    break
            except Exception:
                pass
