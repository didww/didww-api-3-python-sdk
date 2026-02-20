import hashlib
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class Encrypt:
    def __init__(self, public_keys):
        self._public_keys = public_keys

    @staticmethod
    def encrypt_with_keys(binary_data, public_key_pems):
        aes_key = os.urandom(32)
        aes_iv = os.urandom(16)

        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(aes_iv))
        encryptor = cipher.encryptor()
        # PKCS7 padding
        block_size = 16
        pad_len = block_size - (len(binary_data) % block_size)
        padded = binary_data + bytes([pad_len] * pad_len)
        encrypted_aes = encryptor.update(padded) + encryptor.finalize()

        aes_credentials = aes_key + aes_iv

        encrypted_rsa_a = Encrypt._encrypt_rsa_oaep(public_key_pems[0], aes_credentials)
        encrypted_rsa_b = Encrypt._encrypt_rsa_oaep(public_key_pems[1], aes_credentials)

        return encrypted_rsa_a + encrypted_rsa_b + encrypted_aes

    @staticmethod
    def calculate_fingerprint(public_key_pems):
        fp_a = Encrypt._fingerprint_for(public_key_pems[0])
        fp_b = Encrypt._fingerprint_for(public_key_pems[1])
        return f"{fp_a}:::{fp_b}"

    @staticmethod
    def _encrypt_rsa_oaep(pem_key, data):
        public_key = serialization.load_pem_public_key(pem_key.encode("utf-8"))
        return public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    @staticmethod
    def _fingerprint_for(pem_key):
        public_key = serialization.load_pem_public_key(pem_key.encode("utf-8"))
        der_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return hashlib.sha1(der_bytes).hexdigest()
