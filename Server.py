import socket
import threading
import env

# Configuración del servidor de registro
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((env.HOST, env.PORT))
server.listen()

peers = []  # Lista de peers conectados


def handle_client(conn, addr):
    """Maneja la conexión con un cliente (nodo)"""
    try:
        print(f"Conectado a {addr}")
        while True:
            data = conn.recv(1024).decode("utf-8")
            print(data)
            if "[REGISTER]" in data:
                if not data:  # Si no hay datos, el cliente se ha desconectado
                    print(f"Cliente {addr} se ha desconectado")
                    break

                _, ip, port, name = data.split(",")
                peer_info = (ip, int(port), name)

                # Verificar si el peer ya está registrado
                if peer_info not in peers:
                    peers.append(peer_info)
                    print(f"{name} se ha conectado desde {ip}:{port}")

                # Enviar la lista actualizada de peers al nodo
                conn.send(str(peers).encode("utf-8"))

    except Exception as e:
        print(f"Error manejando el cliente {addr}: {e}")
    finally:
        conn.close()  # Asegúrate de cerrar la conexión al final


def receive_connections():
    """Acepta conexiones de nuevos nodos"""
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


print("Registro de servidor escuchando...")
receive_connections()
