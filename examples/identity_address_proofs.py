"""
Example: Create identity, address, and attach proofs with encrypted files.

Demonstrates:
1. Create an identity with a country
2. Create an address linked to the identity
3. Fetch proof types for identity and address
4. Encrypt and upload a PDF file
5. Create proofs attached to identity and address
6. Clean up created resources
"""
import os

from client_factory import create_client
from didww.enums import IdentityType, enum_value
from didww.encrypt import Encrypt
from didww.query_params import QueryParams
from didww.resources.identity import Identity
from didww.resources.address import Address
from didww.resources.country import Country
from didww.resources.proof import Proof
from didww.resources.proof_type import ProofType
from didww.resources.encrypted_file import EncryptedFile

client = create_client()

# --- Step 1: Get a country for the identity ---
countries = client.countries().list().data
country = countries[0]
print(f"Using country: {country.name} ({country.id})")

# --- Step 2: Create an identity ---
identity = Identity()
identity.first_name = "John"
identity.last_name = "Doe"
identity.phone_number = "12125551234"
identity.identity_type = IdentityType.PERSONAL
identity.country = Country.build(country.id)
identity = client.identities().create(identity).data
print(f"Created identity: {identity.id} ({identity.first_name} {identity.last_name})")

# --- Step 3: Create an address linked to the identity ---
address = Address()
address.city_name = "New York"
address.postal_code = "10001"
address.address = "123 Main St"
address.identity = Identity.build(identity.id)
address.country = Country.build(country.id)
address = client.addresses().create(address).data
print(f"Created address: {address.id} ({address.address})")

# --- Step 4: Fetch proof types ---
proof_types = client.proof_types().list().data
identity_proof_type = None
address_proof_type = None
for pt in proof_types:
    if pt.entity_type == enum_value(IdentityType.PERSONAL) and identity_proof_type is None:
        identity_proof_type = pt
    elif pt.entity_type == "Address" and address_proof_type is None:
        address_proof_type = pt
    if identity_proof_type and address_proof_type:
        break

if identity_proof_type:
    print(f"Identity proof type: {identity_proof_type.name} ({identity_proof_type.id})")
else:
    print("No identity proof type found")
if address_proof_type:
    print(f"Address proof type: {address_proof_type.name} ({address_proof_type.id})")
else:
    print("No address proof type found")

# --- Step 5: Encrypt and upload PDF file ---
file_path = os.path.join(os.path.dirname(__file__), "sample.pdf")
with open(file_path, "rb") as f:
    file_content = f.read()

public_keys_response = client.public_keys().list()
pem_keys = [pk.key for pk in public_keys_response.data]
fingerprint = Encrypt.calculate_fingerprint(pem_keys)

# Upload two copies (one for each proof)
files_to_upload = []
for label in ["identity_proof", "address_proof"]:
    encrypted = Encrypt.encrypt_with_keys(file_content, pem_keys)
    files_to_upload.append({
        "data": encrypted,
        "description": f"{label}.pdf",
        "filename": f"{label}.pdf.enc",
    })

file_ids = client.upload_encrypted_files(
    fingerprint=fingerprint,
    files=files_to_upload,
)
print(f"Uploaded encrypted files: {file_ids}")

# --- Step 6: Create proof for identity ---
if identity_proof_type:
    proof = Proof()
    proof.entity = Identity.build(identity.id)
    proof.proof_type = ProofType.build(identity_proof_type.id)
    proof.files = [EncryptedFile.build(file_ids[0])]
    params = QueryParams().include("proof_type")
    created_proof = client.proofs().create(proof, params).data
    print(f"Created identity proof: {created_proof.id} (type={created_proof.proof_type.name})")

# --- Step 7: Create proof for address ---
if address_proof_type:
    proof = Proof()
    proof.entity = Address.build(address.id)
    proof.proof_type = ProofType.build(address_proof_type.id)
    proof.files = [EncryptedFile.build(file_ids[1])]
    params = QueryParams().include("proof_type")
    created_proof = client.proofs().create(proof, params).data
    print(f"Created address proof: {created_proof.id} (type={created_proof.proof_type.name})")

# --- Step 8: Verify - fetch identity and address to check ---
print(f"\nIdentity {identity.id}: verified={identity.verified}")
print(f"Address {address.id}: verified={address.verified}")

# --- Step 9: Clean up ---
print("\nCleaning up...")
client.addresses().delete(address.id)
print(f"  Deleted address: {address.id}")
client.identities().delete(identity.id)
print(f"  Deleted identity: {identity.id}")
for fid in file_ids:
    client.encrypted_files().delete(fid)
    print(f"  Deleted encrypted file: {fid}")

print("\nDone!")
