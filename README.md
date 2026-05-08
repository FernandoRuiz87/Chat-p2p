# 💬 Chat P2P

Una aplicación de **chat en tiempo real con arquitectura peer-to-peer (P2P)**, desarrollada en Python con interfaz gráfica moderna. Los mensajes y archivos se transmiten con **cifrado de extremo a extremo** usando el algoritmo Fernet (AES-128).

---

## 🏗️ Arquitectura

```
┌─────────────┐          ┌─────────────────────────────┐
│             │  REGISTER│                             │
│   Cliente A │◄────────►│   Servidor de Registro      │
│  (chat.py)  │          │      (Server.py)            │
│             │          │  – Mantiene lista de peers  │
└──────┬──────┘          └─────────────────────────────┘
       │  P2P directo
       │ (TCP sockets)
┌──────▼──────┐
│   Cliente B │
│  (chat.py)  │
└─────────────┘
```

El servidor actúa únicamente como **directorio de peers** (Discovery Server). Una vez que los nodos se registran y obtienen la lista de peers activos, la comunicación ocurre **directamente entre clientes** sin pasar por el servidor.

---

## ✨ Características

- 🔒 **Cifrado E2E** — Todos los mensajes se cifran con Fernet (AES-128-CBC + HMAC)
- 👥 **Multiusuario** — Soporte para múltiples peers simultáneos en la misma sala
- 🖼️ **Envío de imágenes** — Transferencia de archivos `.png`, `.jpg`, `.jpeg`, `.gif`
- 🔔 **Notificaciones** — Alertas cuando un usuario entra o sale del chat
- 🎨 **Interfaz gráfica** — UI oscura con `tkinter` + `customtkinter`
- 🧵 **Concurrencia** — Cada conexión P2P se maneja en un hilo independiente
- 🎲 **Puerto dinámico** — Cada cliente escoge un puerto aleatorio (5000–9999)

---

## 📁 Estructura del Proyecto

```
Chat-p2p/
├── Server.py       # Servidor de registro (Discovery Server)
├── chat.py         # Cliente P2P con GUI
├── env.py          # Configuración: HOST, PORT y clave de cifrado
├── Colores.py      # Constantes ANSI para colores en consola
└── images/
    └── logo.png    # Ícono de la aplicación
```

---

## 🛠️ Requisitos

- Python **3.8+**
- Las siguientes dependencias de Python:

| Librería | Uso |
|---|---|
| `customtkinter` | Widgets modernos para la GUI |
| `cryptography` | Cifrado Fernet (AES) |
| `Pillow` | Visualización de imágenes en el chat |
| `tkinter` | Framework base de la interfaz gráfica (incluido en Python) |

---

## ⚙️ Instalación

```bash
# 1. Clona el repositorio
git clone https://github.com/FernandoRuiz87/Chat-p2p.git
cd Chat-p2p

# 2. Instala las dependencias
pip install customtkinter cryptography Pillow
```

---

## 🚀 Uso

### 1. Iniciar el servidor de registro

El servidor debe estar corriendo **antes** de que cualquier cliente intente conectarse.

```bash
python server.py
```

El servidor escuchará en `localhost:8000` de forma predeterminada.

### 2. Iniciar uno o más clientes

Abre una terminal por cada usuario que quieras conectar:

```bash
python chat.py
```

Al iniciar, el cliente:
1. Se conecta al servidor de registro.
2. Muestra una ventana de login para ingresar el nombre de usuario.
3. Se registra y recibe la lista de peers activos.
4. Establece conexiones directas P2P con todos los peers.
5. Abre la ventana del chat.

---

## ⚙️ Configuración (`env.py`)

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `HOST` | `localhost` | Dirección del servidor de registro |
| `PORT` | `8000` | Puerto del servidor de registro |
| `LISTENER_LIMIT` | `5` | Conexiones en cola máximas |
| `KEY` | *(Fernet key)* | Clave simétrica de cifrado compartida |

> **⚠️ Importante:** Todos los clientes y el servidor deben usar la misma `KEY`. Para desplegar en red local o remota, cambia `HOST` a la IP de la máquina que ejecuta el servidor.

---

## 🔐 Seguridad

La comunicación está protegida con **cifrado simétrico Fernet**, que garantiza:
- **Confidencialidad** — Los mensajes no pueden leerse sin la clave.
- **Integridad** — Cualquier modificación en tránsito es detectada (HMAC-SHA256).
- **Autenticidad** — Los datos provienen del remitente legítimo.

> La clave en `env.py` es compartida (pre-shared key). Para producción, se recomienda implementar un esquema de intercambio de claves más robusto (e.g., Diffie-Hellman).

---

## 📸 Interfaz

La aplicación cuenta con dos ventanas:

| Ventana | Descripción |
|---|---|
| **Login** | Pantalla de bienvenida para ingresar el nombre de usuario |
| **Chat** | Sala de chat con panel lateral de usuarios conectados, área de mensajes y controles para enviar texto e imágenes |

### Colores de mensajes

| Color | Significado |
|---|---|
| 🟢 Verde | Mensajes de otros usuarios |
| 🔵 Azul | Tus propios mensajes |
| 🟡 Amarillo | Notificación de nuevo usuario |
| 🔴 Rojo | Notificación de usuario desconectado |
