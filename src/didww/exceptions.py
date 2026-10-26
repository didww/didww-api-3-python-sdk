from enum import Enum


class DidwwError(Exception):
    pass


class DidwwClientError(DidwwError):
    pass


class DidwwApiError(DidwwError):
    def __init__(self, errors, status_code=None):
        self.errors = errors
        self.status_code = status_code
        detail = "; ".join(
            str(e.get("detail", e.get("title", "Unknown error"))) for e in errors
        )
        super().__init__(detail)


class AuthErrorKind(str, Enum):
    """Why an access token could not be obtained."""

    INVALID_REQUEST = "invalid_request"
    INVALID_CLIENT = "invalid_client"
    RATE_LIMITED = "rate_limited"
    SERVER_ERROR = "server_error"
    CONNECTION_ERROR = "connection_error"
    INVALID_GRANT = "invalid_grant"
    UNEXPECTED_STATUS = "unexpected_status"


class DidwwAuthError(DidwwError):
    """The token service did not grant an access token.

    Attributes:
        kind: an ``AuthErrorKind``.
        status_code: the HTTP status of the token service, or None when it did not answer.
        error: the ``error`` code of the answer, or None.
        error_description: the ``error_description`` of the answer, or None.
        retry_after: seconds to wait before the next attempt (``RATE_LIMITED`` only), or None.
    """

    def __init__(self, message=None, *, kind=None, status_code=None, error=None,
                 error_description=None, retry_after=None):
        self.kind = kind
        self.status_code = status_code
        self.error = error
        self.error_description = error_description
        self.retry_after = retry_after
        if message is None:
            message = _auth_message(status_code, error, error_description)
        super().__init__(message)


def _auth_message(status_code, error, error_description):
    if error and error_description:
        return f"Token service: {error}: {error_description}"
    if error or error_description:
        return f"Token service: {error or error_description}"
    return f"Token service responded with status {status_code}"


class PricesErrorKind(str, Enum):
    """Why a prices service call failed."""

    BAD_REQUEST = "bad_request"
    NOT_AUTHORIZED = "not_authorized"
    ACCESS_DENIED = "access_denied"
    PRICE_PLAN_NOT_ASSIGNED = "price_plan_not_assigned"
    PRICE_NOT_FOUND = "price_not_found"
    NOT_ACCEPTABLE = "not_acceptable"
    TOO_MANY_REQUESTS = "too_many_requests"
    SERVICE_UNAVAILABLE = "service_unavailable"
    UNEXPECTED_STATUS = "unexpected_status"
    CONNECTION_ERROR = "connection_error"


class DidwwPricesError(DidwwError):
    """A prices service refused a call or could not be reached.

    Attributes:
        kind: a ``PricesErrorKind``.
        status_code: the HTTP status of the answer, or None when there was no answer.
        code: the ``code`` of the first error object; a 404 without one reports
            ``price_plan_not_assigned``.
        errors: the error objects of the answer, as dicts; empty when it has none.
        retry_after: the Retry-After of the answer in seconds, when given in seconds, or None.
    """

    def __init__(self, message=None, *, kind=None, status_code=None, code=None, errors=None,
                 retry_after=None):
        self.kind = kind
        self.status_code = status_code
        self.code = code
        self.errors = list(errors) if errors else []
        self.retry_after = retry_after
        if message is None:
            message = _prices_message(status_code, self.errors)
        super().__init__(message)


def _prices_message(status_code, errors):
    texts = []
    for error in errors:
        for name in ("detail", "title"):
            value = error.get(name)
            if isinstance(value, str) and value:
                texts.append(value)
                break
    if texts:
        return "Prices service: " + "; ".join(texts)
    if status_code is not None:
        return f"Prices service responded with status {status_code}"
    return "Prices service request failed"
