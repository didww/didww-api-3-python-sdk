import requests
from requests.adapters import HTTPAdapter

from didww.configuration import Environment
from didww.exceptions import DidwwClientError


class DidwwClient:
    API_VERSION = "2022-05-10"

    def __init__(self, api_key, environment=Environment.SANDBOX, base_url=None, session=None):
        if not api_key:
            raise DidwwClientError("API key is required")
        self.api_key = api_key
        self.environment = environment
        self.base_url = base_url or environment.value
        if session is not None:
            # Defensive copy: build a new session preserving settings from the original
            self._session = requests.Session()
            self._session.proxies.update(session.proxies)
            self._session.verify = session.verify
            self._session.cert = session.cert
            self._session.auth = session.auth
            self._session.max_redirects = session.max_redirects
            for prefix, adapter in session.adapters.items():
                self._session.mount(
                    prefix,
                    HTTPAdapter(
                        pool_connections=adapter._pool_connections,
                        pool_maxsize=adapter._pool_maxsize,
                        max_retries=adapter.max_retries,
                        pool_block=adapter._pool_block,
                    ),
                )
        else:
            self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
                "X-DIDWW-API-Version": self.API_VERSION,
            }
        )

    def _url(self, path):
        return f"{self.base_url}/{path}"

    def _auth_headers(self, path):
        if path == "public_keys" or path.startswith("public_keys/"):
            return {}
        return {"Api-Key": self.api_key}

    def get(self, path, params=None):
        resp = self._session.get(self._url(path), params=params, headers=self._auth_headers(path))
        return self._handle_response(resp)

    def post(self, path, data, params=None):
        resp = self._session.post(self._url(path), json=data, params=params, headers=self._auth_headers(path))
        return self._handle_response(resp)

    def patch(self, path, data, params=None):
        resp = self._session.patch(self._url(path), json=data, params=params, headers=self._auth_headers(path))
        return self._handle_response(resp)

    def delete(self, path):
        resp = self._session.delete(self._url(path), headers=self._auth_headers(path))
        if resp.status_code == 204:
            return None
        return self._handle_response(resp)

    def _handle_response(self, resp):
        from didww.exceptions import DidwwApiError

        if resp.status_code >= 400:
            try:
                body = resp.json()
            except ValueError:
                body = {}
            if "errors" in body:
                raise DidwwApiError(body["errors"], status_code=resp.status_code)
            raise DidwwApiError(
                [{"title": f"HTTP {resp.status_code}"}],
                status_code=resp.status_code,
            )
        if not resp.content:
            return None
        return resp.json()

    # --- File upload / download ---

    def upload_encrypted_files(self, fingerprint, files):
        """Upload encrypted files via multipart POST.

        Args:
            fingerprint: Encryption fingerprint string.
            files: List of dicts, each with:
                - 'data' (bytes): encrypted file content
                - 'description' (str, optional): file description
                - 'filename' (str, optional): filename, defaults to 'file.enc'

        Returns:
            List of uploaded file ID strings.
        """
        url = self._url("encrypted_files")
        multipart_fields = [
            ("encrypted_files[encryption_fingerprint]", (None, fingerprint)),
        ]
        for item in files:
            desc = item.get("description", "")
            filename = item.get("filename", "file.enc")
            multipart_fields.append(
                ("encrypted_files[items][][description]", (None, desc)),
            )
            multipart_fields.append(
                ("encrypted_files[items][][file]", (filename, item["data"], "application/octet-stream")),
            )
        resp = self._session.post(
            url,
            files=multipart_fields,
            headers={
                "Accept": "application/json",
                "Content-Type": None,
                "Api-Key": self.api_key,
            },
        )
        if resp.status_code >= 400:
            from didww.exceptions import DidwwApiError

            raise DidwwApiError(
                [{"title": f"HTTP {resp.status_code}"}],
                status_code=resp.status_code,
            )
        body = resp.json()
        if "ids" not in body:
            raise DidwwClientError("Unexpected encrypted_files upload response")
        return body["ids"]

    def download_export(self, url, destination):
        """Download an export CSV file.

        Args:
            url: The full download URL from Export.url attribute.
            destination: File path (str) or writable file-like object.
        """
        resp = self._session.get(
            url,
            headers={
                "Accept": None,
                "Content-Type": None,
                "Api-Key": self.api_key,
            },
            stream=True,
        )
        if resp.status_code >= 400:
            from didww.exceptions import DidwwApiError

            raise DidwwApiError(
                [{"title": f"HTTP {resp.status_code}"}],
                status_code=resp.status_code,
            )
        if isinstance(destination, str):
            with open(destination, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            for chunk in resp.iter_content(chunk_size=8192):
                destination.write(chunk)

    # --- Repository accessors ---

    def countries(self):
        from didww.resources.country import CountryRepository
        return CountryRepository(self)

    def balance(self):
        from didww.resources.balance import BalanceRepository
        return BalanceRepository(self)

    def pops(self):
        from didww.resources.pop import PopRepository
        return PopRepository(self)

    def regions(self):
        from didww.resources.region import RegionRepository
        return RegionRepository(self)

    def cities(self):
        from didww.resources.city import CityRepository
        return CityRepository(self)

    def areas(self):
        from didww.resources.area import AreaRepository
        return AreaRepository(self)

    def did_group_types(self):
        from didww.resources.did_group_type import DidGroupTypeRepository
        return DidGroupTypeRepository(self)

    def did_groups(self):
        from didww.resources.did_group import DidGroupRepository
        return DidGroupRepository(self)

    def available_dids(self):
        from didww.resources.available_did import AvailableDidRepository
        return AvailableDidRepository(self)

    def nanpa_prefixes(self):
        from didww.resources.nanpa_prefix import NanpaPrefixRepository
        return NanpaPrefixRepository(self)

    def proof_types(self):
        from didww.resources.proof_type import ProofTypeRepository
        return ProofTypeRepository(self)

    def public_keys(self):
        from didww.resources.public_key import PublicKeyRepository
        return PublicKeyRepository(self)

    def requirements(self):
        from didww.resources.requirement import RequirementRepository
        return RequirementRepository(self)

    def supporting_document_templates(self):
        from didww.resources.supporting_document_template import SupportingDocumentTemplateRepository
        return SupportingDocumentTemplateRepository(self)

    def capacity_pools(self):
        from didww.resources.capacity_pool import CapacityPoolRepository
        return CapacityPoolRepository(self)

    def did_reservations(self):
        from didww.resources.did_reservation import DidReservationRepository
        return DidReservationRepository(self)

    def shared_capacity_groups(self):
        from didww.resources.shared_capacity_group import SharedCapacityGroupRepository
        return SharedCapacityGroupRepository(self)

    def exports(self):
        from didww.resources.export import ExportRepository
        return ExportRepository(self)

    def addresses(self):
        from didww.resources.address import AddressRepository
        return AddressRepository(self)

    def identities(self):
        from didww.resources.identity import IdentityRepository
        return IdentityRepository(self)

    def encrypted_files(self):
        from didww.resources.encrypted_file import EncryptedFileRepository
        return EncryptedFileRepository(self)

    def dids(self):
        from didww.resources.did import DidRepository
        return DidRepository(self)

    def voice_in_trunk_groups(self):
        from didww.resources.voice_in_trunk_group import VoiceInTrunkGroupRepository
        return VoiceInTrunkGroupRepository(self)

    def voice_out_trunks(self):
        from didww.resources.voice_out_trunk import VoiceOutTrunkRepository
        return VoiceOutTrunkRepository(self)

    def voice_out_trunk_regenerate_credentials(self):
        from didww.resources.voice_out_trunk_regenerate_credential import VoiceOutTrunkRegenerateCredentialRepository
        return VoiceOutTrunkRegenerateCredentialRepository(self)

    def voice_in_trunks(self):
        from didww.resources.voice_in_trunk import VoiceInTrunkRepository
        return VoiceInTrunkRepository(self)

    def orders(self):
        from didww.resources.order import OrderRepository
        return OrderRepository(self)

    def address_verifications(self):
        from didww.resources.address_verification import AddressVerificationRepository
        return AddressVerificationRepository(self)

    def permanent_supporting_documents(self):
        from didww.resources.permanent_supporting_document import PermanentSupportingDocumentRepository
        return PermanentSupportingDocumentRepository(self)

    def proofs(self):
        from didww.resources.proof import ProofRepository
        return ProofRepository(self)

    def requirement_validations(self):
        from didww.resources.requirement_validation import RequirementValidationRepository
        return RequirementValidationRepository(self)
