class DidwwError(Exception):
    pass


class DidwwClientError(DidwwError):
    pass


class DidwwApiError(DidwwError):
    def __init__(self, errors, status_code=None):
        self.errors = errors
        self.status_code = status_code
        detail = "; ".join(
            e.get("detail", e.get("title", "Unknown error")) for e in errors
        )
        super().__init__(detail)
