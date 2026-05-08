import threading
import datetime
import socket
import errno
import json
from os import system
from config.colors import *
import crypto  # Módulo compartido de cifrado (crypto.py)
from config import env

system("cls")


# Configuración del servidor de registro
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((env.HOST, env.PORT))
server.listen()

peers = []  # Lista de peers conectados

# Obtener la fecha y hora actuales
now = datetime.datetime.now()

# Formatear la fecha y hora en un formato legible
hora_conexion = now.strftime("%Y-%m-%d %H:%M:%S")

# Las funciones de cifrado viven en crypto.py para ser compartidas con el cliente

def handle_client(conn, addr):
    """Maneja la conexión con un cliente (nodo)"""
    try:
        peer_info = None  # Inicializa peer_info fuera del bucle
        while True:
            encrypted_data = conn.recv(1024)
            if not encrypted_data:  # Si no hay datos, el cliente cerró la conexión
                break

            data = crypto.decrypt(encrypted_data)  # Descifrar con el módulo compartido

            if "[REGISTER]" in data:
                _, ip, port, name = data.split(",")
                peer_info = (ip, int(port), name)

                # Registrar el peer si no existe ya en la lista
                if peer_info not in peers:
                    peers.append(peer_info)
                    print(
                        f"{GREEN}[CONEXIÓN] {YELLOW}{ip}:{port}{RESET} ~~~ {GREEN}[HORA_CONEXIÓN] {YELLOW}{hora_conexion}{RESET}"
                    )

                # Enviar la lista de peers serializada en JSON (cifrada)
                encrypted_peers = crypto.encrypt(json.dumps(peers))
                conn.send(encrypted_peers)
                
    except socket.error as e:
        if e.errno == errno.WSAECONNRESET:  # Código de error 10054
            pass
    except Exception as e:
        print(f"{PURPLE}Error manejando el cliente {ip}: {e}{RESET}")
    finally:
        if peer_info and peer_info in peers:
            peers.remove(peer_info)  # Elimina el peer de la lista
            print(
                f"{RED}[DESCONEXION] {YELLOW}{ip}:{port}{RESET} ~~~ {RED}[HORA_DESCONEXION] {YELLOW}{hora_conexion}{RESET}"
            )
            # print(f"{BLUE}Lista de peers actualizada: {peers}{RESET}")
        conn.close()


def receive_connections():
    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True  # El hilo muere cuando el programa termina
            thread.start()
    except KeyboardInterrupt:
        print(f"\n{RED}Servidor detenido por el usuario.{RESET}")
    finally:
        server.close()  # Siempre libera el puerto


print(f"Servidor iniciado en {PURPLE}({env.HOST}:{env.PORT}){RESET}\n")
print(f"{CYAN}LOG DEL SERVIDOR{RESET}\n---------------------------------------{RESET}")
receive_connections()
