import base64
import hashlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def compute_file_hash(path):
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def sign_hash_with_rsa(privkey_path: str, data_bytes: bytes) -> str:
    """Подписывает bytes (обычно хэш) приватным ключом RSA, возвращает base64 подпись."""
    with open(privkey_path, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)
    signature = priv.sign(
        data_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode()
