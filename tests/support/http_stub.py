"""Local HTTP servers for wire-level tests (standard library only)."""

import datetime
import json
import os
import socket
import ssl
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")


def fixture_bytes(name):
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()


def fixture_json(name):
    return json.loads(fixture_bytes(name))


class Reply:
    """A scripted answer. ``body`` may be bytes, str or a JSON-serializable object."""

    def __init__(self, status=200, body=b"", headers=None, delay=0.0, content_length=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
            headers = {"Content-Type": "application/json", **(headers or {})}
        elif isinstance(body, str):
            body = body.encode()
        self.status = status
        self.body = body
        self.headers = headers or {}
        self.delay = delay
        self.content_length = content_length


def token_reply(access_token="test-access-token", aud=("api.didww.com",), scope="full",
                api_version="2026-10-22", expires_in=900, **extra):
    body = {"access_token": access_token, "token_type": "Bearer", "expires_in": expires_in,
            "aud": list(aud), "scope": scope, "api_version": api_version, **extra}
    return Reply(200, body)


def jsonapi_reply(status=200, body=None, headers=None):
    if body is None:
        body = {"data": []}
    return Reply(status, json.dumps(body).encode(),
                 {"Content-Type": "application/vnd.api+json", **(headers or {})})


class Recorded:
    def __init__(self, method, path, query, headers, body):
        self.method = method
        self.path = path
        self.query = query
        self.headers = headers
        self.body = body

    def json(self):
        return json.loads(self.body)


class _QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass


class StubServer:
    """A threaded HTTP/1.1 server answering scripted replies per (method, path).

    ``on(method, path, *replies)`` queues replies; the last one is repeated.
    A reply may also be a callable taking the ``Recorded`` request.
    """

    def __init__(self):
        self.requests = []
        self._routes = {}
        self._lock = threading.Lock()
        stub = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def _handle(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                parts = urlsplit(self.path)
                recorded = Recorded(self.command, parts.path, parse_qs(parts.query), dict(self.headers), body)
                reply = stub._next(recorded)
                if reply.delay:
                    time.sleep(reply.delay)
                self.send_response(reply.status)
                for name, value in reply.headers.items():
                    self.send_header(name, value)
                length = reply.content_length if reply.content_length is not None else len(reply.body)
                if "Content-Length" not in reply.headers:
                    self.send_header("Content-Length", str(length))
                self.end_headers()
                if self.command != "HEAD":
                    try:
                        self.wfile.write(reply.body)
                        self.wfile.flush()
                    except OSError:
                        pass
                if reply.content_length is not None and reply.content_length != len(reply.body):
                    self.close_connection = True

            do_GET = do_POST = do_PATCH = do_DELETE = do_PUT = do_HEAD = _handle

        self._server = _QuietServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05},
                                        daemon=True)
        self._thread.start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def on(self, method, path, *replies):
        with self._lock:
            self._routes[(method, path)] = list(replies)
        return self

    def _next(self, recorded):
        with self._lock:
            self.requests.append(recorded)
            queue = self._routes.get((recorded.method, recorded.path))
            if not queue:
                return Reply(404, {"errors": [{"title": "no route"}]})
            reply = queue.pop(0) if len(queue) > 1 else queue[0]
        return reply(recorded) if callable(reply) else reply

    def hits(self, method=None, path=None):
        return [r for r in self.requests
                if (method is None or r.method == method) and (path is None or r.path == path)]

    def close(self):
        self._server.shutdown()
        self._server.server_close()


class RawServer:
    """A socket server running ``script(conn, request_bytes)`` per connection.

    It produces what ``http.server`` cannot: short bodies, stalls, resets,
    TLS failures. ``accepts`` counts the connections.
    """

    def __init__(self, script, read_request=True):
        self.accepts = 0
        self._script = script
        self._read_request = read_request
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(16)
        self._closed = False
        threading.Thread(target=self._serve, daemon=True).start()

    @property
    def port(self):
        return self._sock.getsockname()[1]

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def _serve(self):
        while not self._closed:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                return
            self.accepts += 1
            threading.Thread(target=self._run, args=(conn,), daemon=True).start()

    def _run(self, conn):
        try:
            request = _read_http_request(conn) if self._read_request else b""
            self._script(conn, request)
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def close(self):
        self._closed = True
        try:
            self._sock.close()
        except OSError:
            pass


def _read_http_request(conn):
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(65536)
        if not chunk:
            return data
        data += chunk
    head, _, rest = data.partition(b"\r\n\r\n")
    length = 0
    for line in head.split(b"\r\n")[1:]:
        name, _, value = line.partition(b":")
        if name.strip().lower() == b"content-length":
            length = int(value.strip())
    while len(rest) < length:
        chunk = conn.recv(65536)
        if not chunk:
            break
        rest += chunk
    return head + b"\r\n\r\n" + rest


def http_response(status, body=b"", headers=(), content_length=None):
    """Raw HTTP/1.1 response bytes; ``content_length`` may differ from ``len(body)``."""
    reason = {200: "OK", 401: "Unauthorized", 404: "Not Found", 500: "Internal Server Error"}.get(status, "X")
    lines = [f"HTTP/1.1 {status} {reason}"]
    lines += [f"{name}: {value}" for name, value in headers]
    lines.append(f"Content-Length: {len(body) if content_length is None else content_length}")
    lines.append("Connection: close")
    return ("\r\n".join(lines) + "\r\n\r\n").encode() + body


def self_signed_context():
    """A server ``ssl.SSLContext`` with a fresh self-signed certificate for 127.0.0.1."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    import ipaddress

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
        .sign(key, hashes.SHA256())
    )
    with tempfile.TemporaryDirectory() as d:
        cert_path = os.path.join(d, "cert.pem")
        key_path = os.path.join(d, "key.pem")
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                      serialization.NoEncryption()))
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
    return context
