import socket
import threading

import env

# Configuración del nodo
host = "127.0.0.1"
port = int(input("Enter your port: "))
name = input("Enter your name: ")

peers = []
connections = []  # Lista para almacenar las conexiones de los peers


# Manejar los mensajes entrantes de un peer
def handle_peer(conn, addr):
    while True:
        try:
            message = conn.recv(1024)
            if not message:
                break
            print(f"{addr}: {message.decode('utf-8')}")
        except:
            break
    conn.close()


# Conectar a los peers y mantener las conexiones
def connect_to_peers():
    global connections
    for peer in peers:
        if not port in peer:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((peer[0], peer[1]))
                connections.append(client)  # Almacenar la conexión
                threading.Thread(
                    target=handle_peer, args=(client, (peer[0], peer[1]))
                ).start()
            except Exception as e:
                print(f"Error connecting to peer {peer}: {e}")
                continue


# Enviar mensajes a todos los peers conectados
def send_messages():
    while True:
        message = input(">")  # Leer el mensaje del usuario
        # Mostrar el mensaje localmente en el peer
        print(
            f"{name}: {message}"
        )  # Esto hace que el peer también vea su propio mensaje

        # Enviar el mensaje a todos los peers conectados
        for conn in connections:
            try:
                conn.send(f"{name}: {message}".encode("utf-8"))
            except Exception as e:
                print(f"Error sending message: {e}")


# Registrar el nodo con el servidor de registro
def register_with_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((env.HOST, env.PORT))  # Conectar al servidor de registro
    client.send(
        f"{host},{port},{name}".encode("utf-8")
    )  # Enviar la info del peer al servidor
    data = client.recv(1024).decode("utf-8")  # Recibir la lista de peers
    global peers
    peers = eval(data)  # Actualizar la lista de peers
    client.close()


# Iniciar el servidor para aceptar conexiones entrantes
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"Listening for incoming connections on {host}:{port}")
    while True:
        conn, addr = server.accept()
        connections.append(conn)  # Guardar la nueva conexión entrante
        threading.Thread(target=handle_peer, args=(conn, addr)).start()


# Registrar el nodo con el servidor de registro
register_with_server()

# Conectar a otros nodos
connect_to_peers()

# Iniciar el envío de mensajes en un hilo separado
threading.Thread(target=send_messages).start()

# Iniciar el servidor para aceptar conexiones entrantes en otro hilo
threading.Thread(target=start_server).start()
