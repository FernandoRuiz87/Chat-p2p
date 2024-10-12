import threading
import datetime
import socket
import errno
import env
from os import system
from Colores import *

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


def handle_client(conn, addr):
    """Maneja la conexión con un cliente (nodo)"""
    try:
        peer_info = None  # Inicializa peer_info fuera del bucle
        while True:
            data = conn.recv(1024).decode("utf-8")
            if not data:  # Si no hay datos, el cliente se ha desconectado
                print(
                    f"{RED}DESCONEXION: {YELLOW}{addr}{RESET} - {RED}HORA DE DESCONEXION: {YELLOW}{hora_conexion}{RESET}"
                )
                break

            if "[REGISTER]" in data:
                _, ip, port, name = data.split(",")
                peer_info = (ip, int(port), name)

                # Verificar si el peer ya está registrado
                if peer_info not in peers:
                    peers.append(peer_info)
                    print(
                        f"{GREEN}CONEXIÓN: {YELLOW}{addr}{RESET} - {GREEN}HORA DE CONEXIÓN: {YELLOW}{hora_conexion}{RESET}"
                    )

                # Enviar la lista actualizada de peers al nodo
                conn.send(str(peers).encode("utf-8"))
    except socket.error as e:
        if e.errno == errno.WSAECONNRESET:  # Código de error 10054
            pass
    except Exception as e:
        print(f"{PURPLE}Error manejando el cliente {addr}: {e}{RESET}")
    finally:
        if peer_info and peer_info in peers:
            peers.remove(peer_info)  # Elimina el peer de la lista
            print(
                f"{RED}DESCONEXION: {YELLOW}{addr}{RESET} - {RED}HORA DE DESCONEXION: {YELLOW}{hora_conexion}{RESET}"
            )
            # print(f"{BLUE}Lista de peers actualizada: {peers}{RESET}")
        conn.close()  # Asegúrate de cerrar la conexión al final


def receive_connections():
    """Acepta conexiones de nuevos nodos"""
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


print(f"Servidor iniciado en {PURPLE}({env.HOST}:{env.PORT}){RESET}\n")
print(f"{CYAN}LOG DEL SERVIDOR{RESET}\n---------------------------------------{RESET}")
receive_connections()
