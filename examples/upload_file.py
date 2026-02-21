import os

from client_factory import create_client
from didww.encrypt import Encrypt

client = create_client()

# Use FILE_PATH env var or default to sample.pdf in the same directory
file_path = os.environ.get("FILE_PATH")
if not file_path:
    file_path = os.path.join(os.path.dirname(__file__), "sample.pdf")

with open(file_path, "rb") as f:
    file_content = f.read()

# Fetch public keys from the API
public_keys_response = client.public_keys().list()
pem_keys = [pk.key for pk in public_keys_response.data]

# Encrypt the file
fingerprint = Encrypt.calculate_fingerprint(pem_keys)
encrypted = Encrypt.encrypt_with_keys(file_content, pem_keys)

# Upload
file_ids = client.upload_encrypted_files(
    fingerprint=fingerprint,
    files=[
        {
            "data": encrypted,
            "description": os.path.basename(file_path),
            "filename": os.path.basename(file_path) + ".enc",
        },
    ],
)

print(f"Upload successful!")
print(f"File IDs: {file_ids}")
