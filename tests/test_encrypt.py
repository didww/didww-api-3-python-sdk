from didww.encrypt import Encrypt

# Test public keys from the fixtures
TEST_PUBLIC_KEY_A = """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA0eHGTVjy2s+uOfFteMoB
T6TXa0Ra20weFoA/dQB2SsCvZ2zAOJqDuqbjFPdcRPp0TwR0rmDDHaLzV/d8EwF2
XiX9+9lwEGivn4PCz0A49gelNthD2dFR/TxyiVVdRsiaPeGJKVZTkYO3FhCKBpXe
L2h1t+yhIQGGYZjh/fGgahJf2PKzDapHO4p8MZK8KCUBIN5z20cYblRyt39gdHul
sqGvERDUwYdgiEAFv5Y9yyVFUeMmeiswImLj8yHnVdwc2+5jEtWEeGzkZ0LNQCby
nynlGwzkDXcQ98Pm00XDcvPwPk91dBvZvhA/G2n2zXp8WA+MLOkWIi015Lqy4doa
807DYfJW+600c1P0YaOI/pgGO9dGllpFGcZBxoNN5ZMUUOjTmrXYUNYTGSZh93gd
lGP3rlhvAlui17CUW2pLpl4CaSUDJWXQZyJH/ILZ+HMVgOMsc7eyZDLWyWWaNlJg
EKSVNF3A8zx8oCtu+LjNPTqaiRvc3BI/ISRvb6r99v5oozCVQ/QIT24AxMLdmy01
xOhXuDq48uoUTWssquuOnfFdF1WaK3c+AlaomX39re/rj4pvIB0ZlzuVN+LGG5WK
Yb6jCitvl8lnw9yTBZKZeU1+IFBvWgN72o4B+Y/qjZJ5N0pCK+ZSrIeLo8Pse/S6
QIULNIKq3VuvLgliDcsOzIMCAwEAAQ==
-----END PUBLIC KEY-----"""

TEST_PUBLIC_KEY_B = """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA9L57/eAXG5ILm1CKjDpz
UqqEOq45OyIGXr4lYPPL090C8ulDHkqd8I4Zn1k0ZVLL1SC/mtWaE4+k5jrrQTQN
3pFVDraUsI+ugvtyCwH0IViW0UaASkT26BQwdzN9/iGJACoL1pAOzQaEpBW9LtLB
kgdNYHKZD++RD0gskbkhuaBM5yLx6sK2vES49GhCCog/qGkq9ogZIuXN9UMZpqgv
tF9sBNLixGNxvsz7svxlaPFKim1eetVgWa53KTuypUJcnNWFJdft4NhmOabHfc4M
3IyCtkrkkRmmoaYKr3ZK2fCYIRaUxyEv+YWM3ISV1ZkEEqlRtH2dybOotkxkJpOt
3AKMk86FXrcgMmspf34wN8uFXVrtZht6XkbWWwjlG+I48V1SPM7SK9BrnDQNgoJe
d5LhjyK4dNTJo+XM2C65iwKDc5OzQX+VS9mS5uSKzn9rDOkpjjMLqWxDdmK4X7uZ
ZMkFtDcuf0vYKuMcOQ4w1NH+FcFO1XPtKftIiLLY0SafUIqGEbt1bf0A/whLpTNE
rc1WI1V8+DsYhqZqWDINbqNXS1/iRahiXPanmszR6npkxqdvtMsdM5FJJIz7x9a/
oPNqkDzHWZPwpZCdZO4mijx2CIcMqh8Y2NXlMI/FDlO/qUgmFz1gf9Fm41HLmFzS
5LG5KbxmgbPJlM3Q8s6TAl0CAwEAAQ==
-----END PUBLIC KEY-----"""


class TestEncrypt:
    def test_encrypt_roundtrip(self):
        plaintext = b"Hello, DIDWW!"
        encrypted = Encrypt.encrypt_with_keys(plaintext, [TEST_PUBLIC_KEY_A, TEST_PUBLIC_KEY_B])
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)

    def test_fingerprint_format(self):
        fingerprint = Encrypt.calculate_fingerprint([TEST_PUBLIC_KEY_A, TEST_PUBLIC_KEY_B])
        assert ":::" in fingerprint
        parts = fingerprint.split(":::")
        assert len(parts) == 2
        assert len(parts[0]) == 40  # SHA1 hex digest
        assert len(parts[1]) == 40

    def test_encrypt_different_each_time(self):
        plaintext = b"Test data"
        enc1 = Encrypt.encrypt_with_keys(plaintext, [TEST_PUBLIC_KEY_A, TEST_PUBLIC_KEY_B])
        enc2 = Encrypt.encrypt_with_keys(plaintext, [TEST_PUBLIC_KEY_A, TEST_PUBLIC_KEY_B])
        assert enc1 != enc2  # Random AES key each time
