from pydantic import BaseModel, Field
from typing import Optional, Tuple

import base64
import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes

from src.core.config import settings


def generate_rsa_private_key(
    key_size: int = 2048, passphrase: str | None = None
) -> Tuple[bytes, bytes]:
    """
    Generate a RSA private key along with a public key
    """
    key = RSA.generate(key_size)

    if passphrase:
        private_key: bytes = key.export_key(
            passphrase=passphrase, pkcs=8, protection="scryptAndAES128-CBC"
        )
    else:
        private_key: bytes = key.export_key()

    public_key: bytes = key.publickey().export_key()
    return private_key, public_key


def generate_and_save_rsa_private_key(
    private_key_path: str, key_size: int = 2048, passphrase: str | None = None
) -> Tuple[str, str]:
    """
    Generate a RSA private key and save it to a file
    """
    private_key, public_key = generate_rsa_private_key(key_size, passphrase)
    with open(private_key_path, "wb") as f:
        f.write(private_key)

    public_key_path = f"{private_key_path.replace('.pem', '')}.pub"
    with open(public_key_path, "wb") as f:
        f.write(public_key)
    return private_key_path, public_key_path


def load_rsa_keypair(
    private_key_path: str, passphrase: str | None = None
) -> Tuple[RSA.RsaKey, RSA.RsaKey]:
    """
    Load a RSA private key from a file
    """
    with open(private_key_path, "rb") as f:
        private_key = RSA.import_key(f.read(), passphrase=passphrase)

    public_key_path = f"{private_key_path.replace('.pem', '')}.pub"
    with open(public_key_path, "rb") as f:
        public_key = RSA.import_key(f.read())

    return private_key, public_key


class Encryption:
    priv_key: bytes
    pub_key: bytes

    def __init__(self, priv_key_path: str):
        self.priv_key = load_rsa_keypair(
            priv_key_path, f"{priv_key_path.replace('.pem', '')}.pub"
        )[0]

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data using the RSA public key
        """
        cipher = PKCS1_OAEP.new(self.priv_key)
        base64_data = base64.b64encode(data)
        return cipher.encrypt(base64_data)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data using the RSA private key
        """
        cipher = PKCS1_OAEP.new(self.priv_key)
        base64_data = cipher.decrypt(data)
        return base64.b64decode(base64_data)
