"""
Constantes globales de la aplicación.
Centralizar aquí los valores evita números mágicos esparcidos en el código.
"""

from pathlib import Path
from . import env

# --- Servidor de registro ---
SERVER_HOST = env.HOST
SERVER_PORT = env.PORT

# --- Colores de la UI ---
COLOR_BG_DARK       = "#1E1E1E"
COLOR_BG_MID        = "#434343"
COLOR_BG_LIGHT      = "#737373"
COLOR_ACCENT        = "#29BCF6"
COLOR_ACCENT_HOVER  = "#86E8B5"
COLOR_TEXT_WHITE    = "#FFFFFF"
COLOR_TEXT_GREEN    = "#82e0aa"
COLOR_TEXT_USER     = "#7d3c98"
COLOR_ONLINE        = "#2ecc71"

# Colores de las burbujas de mensaje en el chat
COLOR_MSG_PEER  = "#00FF00"
COLOR_MSG_SELF  = "#00BFFF"
COLOR_MSG_JOIN  = "#f1c40f"
COLOR_MSG_LEAVE = "#e74c3c"

# --- Fuentes ---
FONT_TITLE = ("Typo Round Regular Demo", 12)
FONT_MAIN  = ("Segoe UI", 12)
FONT_LARGE = ("Segoe UI", 20)
FONT_MSG   = ("Segoe UI", 15)
FONT_PEERS = ("Segoe UI", 16)

# --- Geometría de ventanas ---
LOGIN_W,    LOGIN_H    = 325,  350
CHAT_W,     CHAT_H     = 1000, 700
CHAT_MIN_W, CHAT_MIN_H = 800,  650

# --- Rutas de recursos ---
ICON_PATH = str(Path(__file__).parent.parent / "images" / "logo.png")
