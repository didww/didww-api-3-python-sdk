"""
Encrypts a file with the DIDWW public keys and uploads it to encrypted_files.
The returned ID can be attached to a proof (see identity_address_proofs.py).

Usage: DIDWW_API_KEY=xxx [FILE_PATH=/path/to/file] python examples/upload_file.py
"""
import os

from client_factory import create_client
from didww.encrypt import Encrypt

client = create_client()

# Use FILE_PATH env var or default to sample.pdf in the same directory
file_path = os.environ.get("FILE_PATH")
if not file_path:
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample.pdf")

with open(file_path, "rb") as f:
    file_content = f.read()

# Fetch public keys from the API
public_keys_response = client.public_keys().list()
pem_keys = [pk.key for pk in public_keys_response.data]

# Encrypt the file
fingerprint = Encrypt.calculate_fingerprint(pem_keys)
encrypted = Encrypt.encrypt_with_keys(file_content, pem_keys)

# Upload: one file per request
name = os.path.basename(file_path)
file_id = client.upload_encrypted_file(
    fingerprint=fingerprint,
    data=encrypted,
    description=name,
    filename=name + ".enc",
)

print("Upload successful!")
print(f"Encrypted file ID: {file_id}")
