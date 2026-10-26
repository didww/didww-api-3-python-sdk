import copy
import pickle
from datetime import datetime, timezone

import pytest

from didww.auth import AccessToken, MemoryTokenStore, TokenStore
from didww.exceptions import AuthErrorKind, DidwwAuthError, DidwwError
from didww._http import _BearerAuth


def _token(value="secret-access-token", **kwargs):
    return AccessToken(access_token=value, expires_in=900, aud=("api.didww.com",), scope="full",
                       api_version="2026-10-22", **kwargs)


class TestAccessToken:
    def test_repr_and_str_hide_the_access_token(self):
        token = _token()
        for text in (repr(token), str(token), f"{token}", repr([token])):
            assert "secret-access-token" not in text
            assert "[FILTERED]" in text
        assert "api.didww.com" in repr(token)

    def test_is_immutable(self):
        token = _token()
        with pytest.raises(AttributeError):
            token.access_token = "other"

    def test_aud_given_as_string_or_list_becomes_tuple(self):
        assert AccessToken("t", aud="api.didww.com").aud == ("api.didww.com",)
        assert AccessToken("t", aud=["a", "b"]).aud == ("a", "b")
        assert AccessToken("t", aud=None).aud == ()

    def test_dict_round_trip(self):
        minted = datetime(2026, 10, 22, 8, 5, 3, 120000, tzinfo=timezone.utc)
        token = _token(minted_at=minted)
        data = token.to_dict()
        assert data == {
            "access_token": "secret-access-token",
            "token_type": "Bearer",
            "expires_in": 900,
            "aud": ["api.didww.com"],
            "scope": "full",
            "api_version": "2026-10-22",
            "minted_at": "2026-10-22T08:05:03.120000Z",
        }
        assert AccessToken.from_dict(data) == token
        assert AccessToken.from_dict(data).minted_at == minted

    def test_from_dict_accepts_aud_string_and_ignores_unknown_keys(self):
        token = AccessToken.from_dict({"access_token": "t", "aud": "api.didww.com", "extra": 1,
                                       "minted_at": "not a date"})
        assert token.aud == ("api.didww.com",)
        assert token.token_type == "Bearer"
        assert token.minted_at is None

    @pytest.mark.parametrize("data", [
        None,
        {},
        {"access_token": 1},
        {"access_token": "secret-x", "expires_in": True},
        {"access_token": "secret-x", "expires_in": "900"},
        {"access_token": "secret-x", "aud": [1]},
        {"access_token": "secret-x", "scope": 5},
    ])
    def test_from_dict_rejects_wrong_types_without_echoing_the_token(self, data):
        with pytest.raises(ValueError) as exc:
            AccessToken.from_dict(data)
        assert "secret-x" not in str(exc.value)


class TestMemoryTokenStore:
    def test_get_missing(self):
        assert MemoryTokenStore().get("k") is None

    def test_expiry(self):
        now = [100.0]
        store = MemoryTokenStore(clock=lambda: now[0])
        store.set("k", _token(), 900)
        now[0] += 899
        assert store.get("k") is not None
        now[0] += 1
        assert store.get("k") is None

    @pytest.mark.parametrize("ttl", [0, -1, None])
    def test_without_ttl_never_expires(self, ttl):
        now = [0.0]
        store = MemoryTokenStore(clock=lambda: now[0])
        store.set("k", _token(), ttl)
        now[0] += 10 ** 9
        assert store.get("k") is not None

    def test_replace_and_delete(self):
        store = MemoryTokenStore()
        store.set("k", _token("one"), 900)
        store.set("k", _token("two"), 900)
        assert store.get("k").access_token == "two"
        store.delete("k")
        store.delete("k")
        assert store.get("k") is None

    def test_clear(self):
        store = MemoryTokenStore()
        store.set("a", _token(), 0)
        store.clear()
        assert store.get("a") is None

    def test_repr_hides_tokens(self):
        store = MemoryTokenStore()
        store.set("didww:token:v1:abc", _token(), 900)
        assert repr(store) == "MemoryTokenStore(entries=1)"

    def test_is_a_token_store(self):
        assert isinstance(MemoryTokenStore(), TokenStore)

    def test_token_store_is_abstract(self):
        with pytest.raises(TypeError):
            TokenStore()

        class Partial(TokenStore):
            def get(self, key):
                return None

        with pytest.raises(TypeError):
            Partial()


class TestBearerAuth:
    def test_repr_hides_the_token(self):
        auth = _BearerAuth("secret-access-token")
        assert "secret-access-token" not in repr(auth)


class TestDidwwAuthError:
    def test_is_a_didww_error_and_not_an_os_error(self):
        e = DidwwAuthError(kind=AuthErrorKind.SERVER_ERROR, status_code=503)
        assert isinstance(e, DidwwError)
        assert not isinstance(e, OSError)

    @pytest.mark.parametrize("kwargs, message", [
        ({"status_code": 400, "error": "invalid_request", "error_description": "aud is missing"},
         "Token service: invalid_request: aud is missing"),
        ({"status_code": 429, "error": "rate_limit_exceeded"}, "Token service: rate_limit_exceeded"),
        ({"status_code": 200, "error_description": "granted audience [], requested api.didww.com"},
         "Token service: granted audience [], requested api.didww.com"),
        ({"status_code": 503}, "Token service responded with status 503"),
    ])
    def test_message(self, kwargs, message):
        assert str(DidwwAuthError(kind=AuthErrorKind.SERVER_ERROR, **kwargs)) == message

    def test_copy_and_pickle_keep_the_attributes(self):
        e = DidwwAuthError(kind=AuthErrorKind.RATE_LIMITED, status_code=429, error="rate_limit_exceeded",
                           error_description="slow down", retry_after=7)
        for clone in (copy.copy(e), pickle.loads(pickle.dumps(e))):
            assert str(clone) == str(e)
            assert clone.kind is AuthErrorKind.RATE_LIMITED
            assert (clone.status_code, clone.error, clone.error_description, clone.retry_after) == \
                (429, "rate_limit_exceeded", "slow down", 7)
