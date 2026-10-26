import gzip
import logging
import math
import zlib
from importlib.metadata import PackageNotFoundError, version as _pkg_version

from didww import _http, _json
from didww.auth import _DEFAULT_STORE, _TokenProvider
from didww.configuration import (
    DEFAULT_API_VERSION,
    Environment,
    Scope,
    _API_KEY_RE,
    _API_VERSION_RE,
    _AUDIENCE_API,
    _is_service_url,
)
from didww.exceptions import DidwwApiError, DidwwClientError

try:
    _SDK_VERSION = _pkg_version("didww")
except PackageNotFoundError:
    _SDK_VERSION = "0.0.0"

_USER_AGENT = f"didww-python-sdk/{_SDK_VERSION}"
_DEFAULT = object()
_CHUNK = 64 * 1024
_MAX_TIMEOUT = 1_000_000


class DidwwClient:
    """Client of the DIDWW API.

    Requests carry an access token that the client obtains for its API key
    from the token service and keeps in ``token_store``; the API key itself
    is sent only to the token service. One client may be shared by threads.

    Args:
        api_key: The API key: printable ASCII without spaces.
        environment: ``Environment.SANDBOX`` (default) or ``Environment.PRODUCTION``.
        base_url: The JSON:API base URL; defaults to the environment's.
        session: A ``requests.Session`` whose proxies, ``verify``, ``cert`` and
            ``trust_env`` are copied, and of each mounted adapter the pool
            sizes, the blocking flag and ``max_retries`` (kept for JSON:API,
            export and upload calls only). The SDK mounts plain ``HTTPAdapter``
            objects, so custom adapter subclasses are not used; the session
            is never changed or used directly.
        api_version: The API version requested for tokens, ``2026-10-22`` or later.
        scope: ``Scope.READ``, ``Scope.FULL`` or None (no scope is requested and
            the token service grants ``full``).
        token_store: Where tokens are kept; defaults to one in-memory store
            shared by every client of the process.
        logger: A ``logging.Logger`` or ``LoggerAdapter``; defaults to the
            ``didww`` logger.
        auth_url: The token service base URL; defaults to the environment's.
        voice_in_prices_url, voice_out_prices_url, sms_prices_url: The prices
            service base URLs; default to the environment's.
        connect_timeout: Seconds to connect, 10 by default; None for no limit.
        read_timeout: Seconds to wait for each read of an answer, 60 by
            default; None for no limit. There is no limit on a whole download.
    """

    DEFAULT_API_VERSION = DEFAULT_API_VERSION

    def __init__(self, api_key, environment=Environment.SANDBOX, base_url=None, session=None, *,
                 api_version=DEFAULT_API_VERSION, scope=None, token_store=None, logger=None,
                 auth_url=None, voice_in_prices_url=None, voice_out_prices_url=None,
                 sms_prices_url=None, connect_timeout=10.0, read_timeout=60.0):
        if not api_key or not isinstance(api_key, str):
            raise DidwwClientError("API key is required")
        if not _API_KEY_RE.fullmatch(api_key):
            raise DidwwClientError("API key contains characters not allowed in an HTTP header")
        if not isinstance(environment, Environment):
            raise DidwwClientError("environment must be Environment.SANDBOX or Environment.PRODUCTION")
        _check_api_version(api_version)
        scope = _check_scope(scope)
        _check_timeout("connect_timeout", connect_timeout)
        _check_timeout("read_timeout", read_timeout)
        if token_store is None:
            token_store = _DEFAULT_STORE
        elif isinstance(token_store, type) or not all(
                callable(getattr(token_store, m, None)) for m in ("get", "set", "delete")):
            raise DidwwClientError("token_store must provide get, set and delete")
        if logger is None:
            logger = logging.getLogger("didww")
        elif isinstance(logger, type) or not callable(getattr(logger, "log", None)):
            raise DidwwClientError("logger must be a logging.Logger or LoggerAdapter")

        self._api_key = api_key
        self.environment = environment
        self.base_url = _trim(_service_url("API base", base_url or environment.value))
        self._auth_url = _trim(_service_url("Token service", auth_url or environment.auth_url))
        self._voice_in_prices_url = _service_url(
            "Voice IN prices", voice_in_prices_url or environment.voice_in_prices_url)
        self._voice_out_prices_url = _service_url(
            "Voice OUT prices", voice_out_prices_url or environment.voice_out_prices_url)
        self._sms_prices_url = _service_url("SMS prices", sms_prices_url or environment.sms_prices_url)
        self._api_version = api_version
        self._scope = scope
        self._token_store = token_store
        self._logger = logger
        self._timeout = (connect_timeout, read_timeout)
        self._error_body_timeout = read_timeout if read_timeout is not None else _http.DEFAULT_ERROR_BODY_TIMEOUT

        # JSON:API, export and upload calls keep the adapters' max_retries of
        # the session given; token and prices calls are never resent by urllib3.
        self._session = _http.build_session(session, _USER_AGENT, keep_retries=True)
        self._service_session = _http.build_session(session, _USER_AGENT, keep_retries=False)
        self._tokens = _TokenProvider(
            self._service_session, self._auth_url, api_key, api_version,
            scope.value if scope is not None else None, token_store, logger, _USER_AGENT,
        )
        self._transport = _http._Transport(self._session, self._tokens, self._timeout)
        self._service_transport = _http._Transport(self._service_session, self._tokens, self._timeout)

    @property
    def api_key(self):
        """The API key; read-only, build a new client to use another key."""
        return self._api_key

    @property
    def api_version(self):
        """The API version requested for tokens."""
        return self._api_version

    @property
    def scope(self):
        """The scope requested for tokens, or None."""
        return self._scope

    @property
    def auth_url(self):
        """The token service base URL."""
        return self._auth_url

    @property
    def voice_in_prices_url(self):
        return self._voice_in_prices_url

    @property
    def voice_out_prices_url(self):
        return self._voice_out_prices_url

    @property
    def sms_prices_url(self):
        return self._sms_prices_url

    @property
    def token_store(self):
        return self._token_store

    def close(self):
        """Closes the client's connection pools."""
        self._session.close()
        self._service_session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def _url(self, path):
        return f"{self.base_url}/{path}"

    # --- JSON:API ---

    def get(self, path, params=None, *, audience=_DEFAULT):
        return self._request_json("GET", path, params=params, audience=audience)

    def post(self, path, data, params=None, *, audience=_DEFAULT):
        return self._request_json("POST", path, params=params, body=data, audience=audience)

    def patch(self, path, data, params=None, *, audience=_DEFAULT):
        return self._request_json("PATCH", path, params=params, body=data, audience=audience)

    def delete(self, path, *, audience=_DEFAULT):
        return self._request_json("DELETE", path, audience=audience)

    def _request_json(self, method, path, params=None, body=None, audience=_DEFAULT):
        if audience is _DEFAULT:
            audience = None if path == "public_keys" or path.startswith("public_keys/") else _AUDIENCE_API
        headers = {"Accept": _http.JSONAPI_MEDIA_TYPE}
        data = None
        if body is not None:
            data = _json.dumps(body)
            headers["Content-Type"] = _http.JSONAPI_MEDIA_TYPE
        what = f"{method} {path}"
        resp = self._send(self._transport, method, self._url(path), what,
                          audience=audience, headers=headers, params=params, data=data)
        try:
            status = resp.status_code
            if not 200 <= status < 300:
                raise self._api_error(resp)
            if status == 204:
                return None
            content = resp.content
        except _http.READ_ERRORS as e:
            raise DidwwClientError(f"Request {what} failed: {type(e).__name__}") from _http.detached(e)
        finally:
            resp.close()
        if not content:
            return None
        document = _parse_json(content)
        if document is _INVALID:
            raise DidwwClientError(f"Request {what} returned a body that is not valid JSON")
        return document

    def _send(self, transport, method, url, what, **kwargs):
        try:
            return transport.request(method, url, **kwargs)
        except _http.READ_ERRORS as e:
            raise DidwwClientError(f"Request {what} failed: {type(e).__name__}") from _http.detached(e)

    def _api_error(self, resp):
        status = resp.status_code
        document = _parse_json(_http.read_error_body(resp, self._error_body_timeout))
        errors = None
        if isinstance(document, dict) and isinstance(document.get("errors"), list):
            errors = [e for e in document["errors"] if isinstance(e, dict)]
        if not errors:
            errors = [{"title": f"HTTP {status}"}]
        return DidwwApiError(errors, status_code=status)

    # --- File upload / download ---

    def upload_encrypted_file(self, fingerprint, data, description=None, filename="file.enc"):
        """Upload a single encrypted file via multipart POST.

        The body is built in memory, so it can be sent once more with a new
        access token when the API refuses the current one.

        Args:
            fingerprint: Encryption fingerprint string.
            data: Encrypted file content: bytes, or a binary file object, which is read once.
            description: Optional file description.
            filename: Filename, defaults to 'file.enc'.

        Returns:
            The created resource ID string.

        Raises:
            DidwwApiError: The API refused the upload.
            DidwwClientError: The request failed or the answer is unexpected.
        """
        if isinstance(data, (bytes, bytearray, memoryview)):
            content = bytes(data)
        elif callable(getattr(data, "read", None)):
            content = data.read()
            if not isinstance(content, (bytes, bytearray)):
                raise TypeError("data must be bytes or a binary file object")
            content = bytes(content)
        else:
            raise TypeError("data must be bytes or a binary file object")
        multipart_fields = [
            ("encrypted_files[encryption_fingerprint]", (None, fingerprint)),
            ("encrypted_files[file]", (filename, content, "application/octet-stream")),
        ]
        if description:
            multipart_fields.append(
                ("encrypted_files[description]", (None, description)),
            )
        what = "POST encrypted_files"
        resp = self._send(self._transport, "POST", self._url("encrypted_files"), what,
                          audience=_AUDIENCE_API, headers={"Accept": "application/json"},
                          files=multipart_fields)
        try:
            if not 200 <= resp.status_code < 300:
                raise self._api_error(resp)
            body = resp.content
        except _http.READ_ERRORS as e:
            raise DidwwClientError(f"Request {what} failed: {type(e).__name__}") from _http.detached(e)
        finally:
            resp.close()
        document = _parse_json(body)
        if not isinstance(document, dict) or not isinstance(document.get("data"), dict) \
                or "id" not in document["data"]:
            raise DidwwClientError("Unexpected encrypted_files upload response")
        return document["data"]["id"]

    def download_export(self, url, dest):
        """Download an export file (.csv.gz) unchanged.

        The access token is sent only to the origin (scheme, host and port)
        of the API base URL or of the environment, as the API builds export
        URLs on the environment's host: a URL on any other origin raises
        ``DidwwClientError`` without a request. Redirects are not followed
        and only a 200 answer is written; any other status raises
        ``DidwwApiError``.

        Args:
            url: The full download URL from the Export.url attribute.
            dest: A file path, written through a temporary file next to it
                that replaces it only once the whole file has arrived; or a
                binary file object, written as the data arrives and left open.

        Raises:
            DidwwClientError: The URL is refused, or the download failed or was cut short.
            DidwwApiError: The API answered with another status than 200.
            OSError: The destination could not be written.
        """
        self._download_export(url, dest, decompress=False)

    def download_and_decompress_export(self, url, dest):
        """Download a gzip-compressed export (.csv.gz) and write the decompressed CSV.

        The URL, the answer and ``dest`` are handled as in ``download_export``;
        the data is decompressed as it arrives.

        Raises:
            DidwwClientError: The URL is refused, or the download or the decompression failed.
            DidwwApiError: The API answered with another status than 200.
            OSError: The destination could not be written.
        """
        self._download_export(url, dest, decompress=True)

    def _download_export(self, url, dest, decompress):
        to_path = _http.is_destination_path(dest)
        if not to_path and not callable(getattr(dest, "write", None)):
            raise TypeError("dest must be a file path or a binary file object")
        self._check_export_url(url)
        resp = self._send(self._transport, "GET", url, "GET export", audience=_AUDIENCE_API,
                          headers={"Accept": None, "Accept-Encoding": "identity"})
        try:
            if resp.status_code != 200:
                raise self._api_error(resp)
            if to_path:
                with _http.AtomicFile(dest) as target:
                    self._copy_export(resp, target.file.write, decompress)
                    target.commit()
            else:
                self._copy_export(resp, dest.write, decompress)
        finally:
            resp.close()

    def _copy_export(self, resp, write, decompress):
        expected = _http.content_length(resp)
        if not decompress:
            try:
                count = _http.copy_raw(resp, write)
            except _http.BodyReadError as e:
                raise _export_read_error(e) from _http.detached(e.cause)
            _check_complete(count, expected)
            return

        reader = _http.RawReader(resp)
        with gzip.GzipFile(fileobj=reader, mode="rb") as gz:
            while True:
                failure = None
                try:
                    chunk = gz.read(_CHUNK)
                except _http.BodyReadError as e:
                    raise _export_read_error(e) from _http.detached(e.cause)
                except (EOFError, OSError, zlib.error) as e:
                    failure = e
                if failure is not None:
                    if reader.eof and expected is not None and reader.count != expected:
                        raise DidwwClientError(_incomplete_message(reader.count, expected))
                    raise DidwwClientError("Failed to decompress export data") from failure
                if not chunk:
                    break
                _http.write_all(write, chunk)
        _check_complete(reader.count, expected)
        if reader.count == 0:
            raise DidwwClientError("Failed to decompress export data: the export is empty")

    def _check_export_url(self, url):
        target = _http.origin(url)
        base = _http.origin(self.base_url)
        environment = _http.origin(self.environment.value)
        if target is not None and target in (base, environment):
            return
        shown = _http.format_origin(target) if target is not None \
            else "that is not an absolute http or https URL without user info"
        raise DidwwClientError(
            f"Export URL {shown} does not match the API base URL {_http.format_origin(base)}"
            f" or the environment URL {_http.format_origin(environment)}"
        )

    # --- Repository accessors ---

    def countries(self):
        from didww.resources.country import CountryRepository
        return CountryRepository(self)

    def balance(self):
        from didww.resources.balance import BalanceRepository
        return BalanceRepository(self)

    def regions(self):
        from didww.resources.region import RegionRepository
        return RegionRepository(self)

    def cities(self):
        from didww.resources.city import CityRepository
        return CityRepository(self)

    def areas(self):
        from didww.resources.area import AreaRepository
        return AreaRepository(self)

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

    def address_requirements(self):
        from didww.resources.address_requirement import AddressRequirementRepository
        return AddressRequirementRepository(self)

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

    def did_history(self):
        from didww.resources.did_history import DidHistoryRepository
        return DidHistoryRepository(self)

    def emergency_requirements(self):
        from didww.resources.emergency_requirement import EmergencyRequirementRepository
        return EmergencyRequirementRepository(self)

    def emergency_requirement_validations(self):
        from didww.resources.emergency_requirement_validation import EmergencyRequirementValidationRepository
        return EmergencyRequirementValidationRepository(self)

    def emergency_calling_services(self):
        from didww.resources.emergency_calling_service import EmergencyCallingServiceRepository
        return EmergencyCallingServiceRepository(self)

    def emergency_verifications(self):
        from didww.resources.emergency_verification import EmergencyVerificationRepository
        return EmergencyVerificationRepository(self)

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

    def sms_trunks(self):
        from didww.resources.sms_trunk import SmsTrunkRepository
        return SmsTrunkRepository(self)

    def sms_trunk_groups(self):
        from didww.resources.sms_trunk_group import SmsTrunkGroupRepository
        return SmsTrunkGroupRepository(self)

    def sms_trunk_regenerate_credentials(self):
        from didww.resources.sms_trunk_regenerate_credential import SmsTrunkRegenerateCredentialRepository
        return SmsTrunkRegenerateCredentialRepository(self)

    def sender_id_verifications(self):
        from didww.resources.sender_id_verification import SenderIdVerificationRepository
        return SenderIdVerificationRepository(self)

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

    def address_requirement_validations(self):
        from didww.resources.address_requirement_validation import AddressRequirementValidationRepository
        return AddressRequirementValidationRepository(self)

    # --- Prices ---

    def voice_in_prices(self):
        """The Voice IN price list. Lookup filters: ``number`` (required), ``src_country_iso``."""
        from didww.prices._service import VOICE_IN, PricesService
        return PricesService(self, VOICE_IN)

    def voice_out_prices(self):
        """The Voice OUT price list. Lookup filters: ``number`` (required)."""
        from didww.prices._service import VOICE_OUT, PricesService
        return PricesService(self, VOICE_OUT)

    def sms_out_a2p_prices(self):
        """The SMS OUT A2P price list. Lookup filters: ``dst_number``, ``dst_country_iso`` (one at least)."""
        from didww.prices._service import SMS_OUT_A2P, PricesService
        return PricesService(self, SMS_OUT_A2P)

    def sms_out_p2p_prices(self):
        """The SMS OUT P2P price list. Lookup filters: ``dst_number``, ``dst_country_iso`` (one at least)."""
        from didww.prices._service import SMS_OUT_P2P, PricesService
        return PricesService(self, SMS_OUT_P2P)

    def sms_out_otp_prices(self):
        """The SMS OUT OTP price list. Lookup filters: ``dst_number``, ``dst_country_iso`` (one at least)."""
        from didww.prices._service import SMS_OUT_OTP, PricesService
        return PricesService(self, SMS_OUT_OTP)

    def sms_in_prices(self):
        """The SMS IN price list. Lookup filters: ``dst_number``, ``dst_country_iso`` (one at least)."""
        from didww.prices._service import SMS_IN, PricesService
        return PricesService(self, SMS_IN)


_INVALID = object()


def _parse_json(body):
    try:
        return _json.loads(body)
    except (ValueError, RecursionError):
        pass
    return _INVALID


def _trim(url):
    return url[:-1] if url.endswith("/") else url


def _service_url(name, url):
    if not _is_service_url(url):
        if isinstance(url, str):
            text = url
        elif isinstance(url, (bytes, bytearray)):
            text = url.decode("latin-1")
        else:
            text = str(url)
        shown = "a URL with user info" if "@" in text else repr(url)
        raise DidwwClientError(
            f"{name} URL must be an http or https URL without a query or fragment, got {shown}")
    return url


def _check_api_version(api_version):
    if not isinstance(api_version, str) or not _API_VERSION_RE.fullmatch(api_version):
        raise DidwwClientError(f"API version must be a YYYY-MM-DD date, got {api_version!r}")
    if api_version < DEFAULT_API_VERSION:
        raise DidwwClientError(
            f"API version {api_version} is not supported: this SDK requires {DEFAULT_API_VERSION}"
            " or later; use didww 3.x (branch release-3) for 2026-04-16"
        )


def _check_scope(scope):
    if scope is None:
        return None
    if isinstance(scope, str):
        try:
            return Scope(scope)
        except ValueError:
            pass
    raise DidwwClientError("scope must be Scope.READ, Scope.FULL or None")


def _check_timeout(name, value):
    if value is None:
        return
    message = f"{name} must be a positive number of seconds up to {_MAX_TIMEOUT} or None"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DidwwClientError(message)
    try:
        seconds = float(value)
    except OverflowError:
        seconds = math.inf
    if not math.isfinite(seconds) or seconds <= 0 or seconds > _MAX_TIMEOUT:
        raise DidwwClientError(message)


def _incomplete_message(count, expected):
    return f"Export data is incomplete: received {count} of {expected} bytes"


def _check_complete(count, expected):
    if expected is not None and count != expected:
        raise DidwwClientError(_incomplete_message(count, expected))


def _export_read_error(error):
    if error.incomplete:
        return DidwwClientError("Export data is incomplete")
    return DidwwClientError(f"Failed to read export data: {type(error.cause).__name__}")
