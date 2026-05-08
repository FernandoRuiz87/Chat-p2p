"""
Módulo de cifrado compartido entre el cliente y el servidor.

Provee funciones de alto nivel para cifrar y descifrar cadenas de texto
usando el algoritmo Fernet (AES-128-CBC + HMAC-SHA256).
"""

from cryptography.fernet import Fernet
from config import env

# Instancia única del cifrador, inicializada con la clave del entorno
_cipher = Fernet(env.KEY)


def encrypt(data: str) -> bytes:
    """Cifra una cadena UTF-8 y devuelve los bytes cifrados."""
    return _cipher.encrypt(data.encode())


def decrypt(data: bytes) -> str:
    """Descifra bytes y devuelve la cadena UTF-8 original."""
    return _cipher.decrypt(data).decode()
