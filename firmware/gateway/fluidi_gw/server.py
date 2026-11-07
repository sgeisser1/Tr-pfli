"""HTTP-Schicht: HTTPS-App-Server (PWA + API + SSE), HTTP-Port 80 (Weiterleitung, CA-Zertifikat) und
öffentliches Dashboard auf eigenem HTTP-Port (nur lesen, abschaltbar, D-020).

Sicherheitsregeln wie GATEWAY_API Kap. 3: Cookie-Sitzung (HttpOnly, Secure, SameSite=Strict), CSRF-Header,
Origin-Prüfung, Sperre nach Fehlversuchen, elevate für heikle Aktionen, CSP ohne Inline-Skripte, kein HSTS.
"""
from __future__ import annotations

import gzip
import hashlib
import hmac
import io
import json
import logging
import math
import mimetypes
import os
import queue
import re
import secrets
import ssl
import struct
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import api, crypto, pki
from .model import ApiError, iso, now

log = logging.getLogger("fluidi.http")
API = "/api/v1"
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; "
       "manifest-src 'self'; worker-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
STATIC_ALLOW = {"index.html", "manifest.webmanifest", "sw.js", "favicon.ico", "dashboard.html"}
STATIC_DIRS = {"css", "js", "vendor", "icons", "img", "data"}
DASH_FILES = re.compile(r"^(dashboard\.html|css/app\.css|js/(dom|art|board|dashboard)\.js|img/[a-z0-9-]+\.svg|"
                        r"icons/[a-z0-9-]+\.(png|ico)|data/species\.json)$")
SESSION_SHORT, SESSION_LONG, ELEVATE_S = 12 * 3600, 30 * 86400, 300
LOCK_AFTER, LOCK_BASE_S, LOCK_MAX_S, GLOBAL_FAILS_PER_MIN = 5, 60, 900, 20
MAX_SESSIONS = 8
MAX_STREAMS = 4

mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/svg+xml", ".svg")


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 32


class Base(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "fluidi"
    sys_version = ""
    M = None
    CTL = None
    QUIET = True

    def log_message(self, fmt, *args):
        if not self.QUIET:
            log.info("%s %s", self.address_string(), fmt % args)

    def client_ip(self):
        return self.client_address[0]

    def common(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

    def send_json(self, status, obj, headers=None):
        data = b"" if obj is None else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.common()
        if obj is not None:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_bytes(self, status, data, ctype, headers=None):
        self.send_response(status)
        self.common()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_stream(self, status, chunks, ctype, headers=None):
        """Antwort ohne Gesamtpuffer (CSV-Export): chunked transfer encoding."""
        self.send_response(status)
        self.common()
        self.send_header("Content-Type", ctype)
        self.send_header("Transfer-Encoding", "chunked")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command == "HEAD":
            return
        for c in chunks:
            if c:
                self.wfile.write(f"{len(c):X}\r\n".encode() + c + b"\r\n")
        self.wfile.write(b"0\r\n\r\n")

    def static(self, path, allow=None):
        app = Path(self.M.cfg.app_dir).resolve()
        if path in ("", "/"):
            path = "/index.html"
        rel = path.lstrip("/")
        parts = rel.split("/")
        ok = allow(rel) if allow else (rel in STATIC_ALLOW or parts[0] in STATIC_DIRS)
        if ".." in parts or not ok:
            raise ApiError(404, "not_found", "Nicht gefunden")
        f = (app / rel).resolve()
        if not str(f).startswith(str(app) + os.sep) or not f.is_file():
            raise ApiError(404, "not_found", "Nicht gefunden")
        data = f.read_bytes()
        ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "application/manifest+json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        etag = '"' + hashlib.sha256(data).hexdigest()[:16] + '"'
        h = {"Cache-Control": "no-cache", "ETag": etag}
        if rel == "sw.js":
            h["Service-Worker-Allowed"] = "/"
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.common()
            for k, v in h.items():
                self.send_header(k, v)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if "gzip" in (self.headers.get("Accept-Encoding") or "") and len(data) > 1024 and not ctype.startswith("image/png"):
            data = gzip.compress(data, 6)
            h["Content-Encoding"] = "gzip"
            h["Vary"] = "Accept-Encoding"
        self.send_bytes(200, data, ctype, h)

    def error_out(self, e: ApiError):
        h = {"Retry-After": str(e.retry_after)} if e.retry_after is not None else None
        self.send_json(e.status, e.body(), h)


# ============================================================================== App (HTTPS)
class AppHandler(Base):
    HTTPS = True

    @property
    def server_ctl(self):
        return self.CTL

    def do_GET(self):
        self.dispatch()

    do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_GET

    def dispatch(self):
        url = urlsplit(self.path)
        try:
            if url.path.startswith(API + "/") or url.path == API:
                self.api(url)
            elif self.command in ("GET", "HEAD"):
                self.static(url.path)
            else:
                raise ApiError(405, "bad_request", "Methode nicht erlaubt")
        except ApiError as e:
            self.error_out(e)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # noqa: BLE001
            log.exception("Fehler bei %s %s", self.command, self.path)
            try:
                self.send_json(500, {"error": {"code": "internal", "message": f"Interner Fehler: {e.__class__.__name__}"}})
            except OSError:
                pass

    # -------------------------------------------------------------- Sitzungen
    def _token(self):
        m = re.search(r"(?:^|;\s*)fluidi_sid=([A-Za-z0-9_\-]+)", self.headers.get("Cookie") or "")
        return m.group(1) if m else None

    def session(self):
        tok = self._token()
        if not tok:
            return None
        th = hashlib.sha256(tok.encode()).hexdigest()
        s = self.M.sessions.get(th)
        if not s or s["expires"] < now():
            if s:
                self.M.sessions.pop(th, None)
                self.M.store.delete_session(th)
            return None
        s["_th"] = th
        return s

    def save_session(self, s):
        doc = {k: v for k, v in s.items() if k != "_th"}
        self.M.sessions[s["_th"]] = s
        self.M.store.save_session(s["_th"], doc)

    def new_session(self, remember=False):
        M = self.M
        tok = secrets.token_urlsafe(24)
        th = hashlib.sha256(tok.encode()).hexdigest()
        life = SESSION_LONG if remember else SESSION_SHORT
        s = {"csrf": secrets.token_urlsafe(18), "expires": now() + life, "elevated_until": now() + ELEVATE_S,
             "remember": remember, "created": now(), "_th": th}
        if len(M.sessions) >= MAX_SESSIONS:
            oldest = min(M.sessions, key=lambda k: M.sessions[k].get("created", 0))
            M.sessions.pop(oldest)
            M.store.delete_session(oldest)
        self.save_session(s)
        M.fails.pop(self.client_ip(), None)
        cookie = f"fluidi_sid={tok}; Path=/; HttpOnly; SameSite=Strict"
        if remember:
            cookie += f"; Max-Age={life}"
        if self.HTTPS:
            cookie += "; Secure"
        return s, {"Set-Cookie": cookie}

    def end_session(self):
        s = self.session()
        if s:
            self.M.sessions.pop(s["_th"], None)
            self.M.store.delete_session(s["_th"])

    def end_other_sessions(self):
        s = self.session()
        keep = s["_th"] if s else ""
        for k in list(self.M.sessions):
            if k != keep:
                self.M.sessions.pop(k)
        self.M.store.delete_session(keep=keep)

    @staticmethod
    def session_body(s):
        return {"csrf": s["csrf"], "expires": iso(s["expires"]),
                "elevated_until": iso(s["elevated_until"]) if (s.get("elevated_until") or 0) > now() else None}

    def lock_check(self):
        M = self.M
        t = now()
        M.global_fails = [x for x in M.global_fails if t - x < 60]
        f = M.fails.get(self.client_ip())
        if f and f.get("until", 0) > t:
            ra = int(math.ceil(f["until"] - t))
            raise ApiError(429, "locked", f"Zu viele Fehlversuche. Bitte {ra} s warten.", retry_after=ra)
        if len(M.global_fails) >= GLOBAL_FAILS_PER_MIN:
            raise ApiError(429, "locked", "Zu viele Fehlversuche im Netz. Bitte 60 s warten.", retry_after=60)

    def lock_fail(self):
        M = self.M
        t = now()
        M.global_fails.append(t)
        f = M.fails.setdefault(self.client_ip(), {"n": 0, "until": 0})
        f["n"] += 1
        if f["n"] >= LOCK_AFTER:
            f["until"] = t + min(LOCK_MAX_S, LOCK_BASE_S * 2 ** (f["n"] - LOCK_AFTER))
        M.log("warn", "login_failed", f"Anmeldung fehlgeschlagen von {self.client_ip()} ({f['n']}×)")

    def check_auth(self, auth, elevated):
        s = self.session()
        if auth == "public":
            return s
        if auth == "read":
            if self.M.settings["public_read"] or s:
                return s
            raise ApiError(401, "auth_required", "Bitte anmelden")
        if not s:
            raise ApiError(401, "auth_required", "Bitte anmelden")
        if auth == "write":
            if not hmac.compare_digest(self.headers.get("X-CSRF-Token") or "", s["csrf"]):
                raise ApiError(403, "csrf", "Sicherheitsprüfung fehlgeschlagen, Seite neu laden")
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != (self.headers.get("Host") or ""):
                raise ApiError(403, "forbidden", "Fremde Herkunft abgelehnt")
        if elevated and (s.get("elevated_until") or 0) < now():
            raise ApiError(403, "elevation_required", "Bitte Passwort erneut bestätigen")
        return s

    def read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 4 * 1024 * 1024:
            raise ApiError(413, "too_large", "Datei zu gross")
        return self.rfile.read(n) if n else b""

    def api(self, url):
        sub = url.path[len(API):] or "/"
        for method, tpl, rx, fn, auth, elevated in api.ROUTES:
            m = rx.match(sub)
            if not m or (method != self.command and not (self.command == "HEAD" and method == "GET")):
                continue
            sess = self.check_auth(auth, elevated)
            raw = self.read_body() if self.command in ("POST", "PUT", "PATCH", "DELETE") else b""
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
            body = None
            if raw and ctype == "application/json":
                try:
                    body = json.loads(raw)
                except ValueError:
                    raise ApiError(400, "bad_request", "Ungültiges JSON")
                if not isinstance(body, dict):
                    raise ApiError(400, "bad_request", "JSON-Objekt erwartet")
            elif raw and ctype != "application/octet-stream":
                raise ApiError(415 if ctype else 400, "bad_request", "Content-Type muss application/json sein")
            q = {k: v[-1] for k, v in parse_qs(url.query).items()}
            if fn is api.stream:
                return fn(self, sess=sess, q=q, body={}, **m.groupdict())
            with self.M.lock:
                return fn(self, sess=sess, q=q, body=body if body is not None else ({} if not raw else raw), **m.groupdict())
        if any(rx.match(sub) for _, _, rx, *_ in api.ROUTES):
            raise ApiError(405, "bad_request", "Methode nicht erlaubt")
        raise ApiError(404, "not_found", "Unbekannter Endpunkt")

    def sse(self):
        M = self.M
        if len(M.sse_clients) >= MAX_STREAMS:
            raise ApiError(503, "busy", "Zu viele Live-Verbindungen")
        qu: queue.Queue = queue.Queue(maxsize=200)
        M.sse_clients.append(qu)
        try:
            self.send_response(200)
            self.common()
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            self.wfile.write(b"retry: 5000\n: fluidi\n\n")
            self.wfile.flush()
            while not self.CTL or not self.CTL.stopping.is_set():
                try:
                    self.wfile.write(qu.get(timeout=15).encode())
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            if qu in M.sse_clients:
                M.sse_clients.remove(qu)


# ============================================================================== Port 80
class RedirectHandler(Base):
    """Nur: Weiterleitung auf HTTPS, CA-Zertifikat, Seite mit Fingerabdruck (GATEWAY_API 3.1)."""

    def do_GET(self):
        url = urlsplit(self.path)
        tls = self.M.cfg.tls_path
        if url.path in ("/ca.crt", "/ca.der"):
            p = Path(tls, "ca.der")
            if not p.exists():
                return self.send_json(404, {"error": {"code": "not_found", "message": "Noch kein Zertifikat"}})
            return self.send_bytes(200, p.read_bytes(), "application/x-x509-ca-cert",
                                   {"Content-Disposition": 'attachment; filename="fluidi-ca.crt"', "Cache-Control": "no-store"})
        if url.path in ("/ca", "/einrichten"):
            try:
                fp = pki.fingerprint(tls)
            except OSError:
                fp = "(noch kein Zertifikat)"
            html = (f"<!doctype html><html lang=\"de-CH\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" "
                    f"content=\"width=device-width, initial-scale=1\"><title>fluidi – Zertifikat</title></head><body>"
                    f"<h1>fluidi – Zertifikat installieren</h1><p>1. <a href=\"/ca.crt\">CA-Zertifikat laden</a> und auf dem "
                    f"Gerät als <b>CA-Zertifikat</b> installieren (Anleitung: GATEWAY_SETUP.md, Kap. 6).</p>"
                    f"<p>2. Fingerabdruck vergleichen (SHA-256), muss mit der Anzeige bei der Installation übereinstimmen:</p>"
                    f"<p><code>{fp}</code></p><p>3. Danach: <a href=\"https://{self.M.cfg.hostname}/\">https://{self.M.cfg.hostname}/</a></p>"
                    f"</body></html>").encode()
            return self.send_bytes(200, html, "text/html; charset=utf-8", {"Cache-Control": "no-store"})
        host = self.M.cfg.hostname
        self.send_response(301)
        self.common()
        self.send_header("Location", f"https://{host}{url.path if url.path.startswith('/') else '/'}")
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_HEAD = do_GET


# ============================================================================== Dashboard-Port (D-020)
class DashboardHandler(Base):
    """Öffentliche Nur-Lese-Ansicht: nur GET, nur Dashboard-Dateien und GET /api/v1/dashboard. Keine Cookies,
    keine Sensor-IDs, keine Systemdaten. Rate-Limit 120 Anfragen/min je IP."""
    hits: dict = {}

    def do_GET(self):
        url = urlsplit(self.path)
        try:
            ip, t = self.client_ip(), time.time()
            h = [x for x in self.hits.get(ip, []) if t - x < 60]
            h.append(t)
            self.hits[ip] = h
            if len(h) > 120:
                raise ApiError(429, "locked", "Zu viele Anfragen", retry_after=60)
            d = self.M.settings["dashboard"]
            if not (d["enabled"] and d["public"]):
                raise ApiError(404, "not_found", "Dashboard ist nicht freigegeben")
            if url.path == API + "/dashboard":
                with self.M.lock:
                    return self.send_json(200, api.dashboard_data(self.M))
            p = "/dashboard.html" if url.path in ("", "/") else url.path
            self.static(p, allow=lambda rel: bool(DASH_FILES.match(rel)))
        except ApiError as e:
            self.error_out(e)
        except (BrokenPipeError, ConnectionResetError):
            pass

    do_HEAD = do_GET

    def do_POST(self):
        self.error_out(ApiError(405, "bad_request", "Nur lesen"))

    do_PUT = do_PATCH = do_DELETE = do_POST


# ============================================================================== Steuerung
class ServerCtl:
    def __init__(self, model, cfg):
        self.M = model
        self.cfg = cfg
        self.stopping = threading.Event()
        self.servers = {}
        self._dash_port = None

    def _serve(self, name, port, handler, ctx=None):
        cls = type(handler.__name__, (handler,), {"M": self.M, "CTL": self, "QUIET": self.cfg.quiet})
        srv = Server((self.cfg.host, port), cls)
        if ctx:
            srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        threading.Thread(target=srv.serve_forever, name=f"http-{name}", daemon=True).start()
        self.servers[name] = srv
        return srv

    def start(self):
        ctx = None
        if self.cfg.tls:
            ctx = pki.server_context(self.cfg.tls_path)
        app = self._serve("app", self.cfg.https_port, AppHandler, ctx)
        AppHandler.HTTPS = bool(ctx)
        if self.cfg.tls and self.cfg.http_port:
            self._serve("redirect", self.cfg.http_port, RedirectHandler)
        self.dashboard_changed()
        return app

    def dashboard_changed(self):
        d = self.M.settings["dashboard"]
        want = self.cfg.dashboard_port if (d["enabled"] and d["public"] and self.cfg.dashboard_port) else None
        if want == self._dash_port:
            return
        old = self.servers.pop("dashboard", None)
        if old:
            threading.Thread(target=old.shutdown, daemon=True).start()
            old.server_close()
        self._dash_port = None
        if want:
            try:
                self._serve("dashboard", want, DashboardHandler)
                self._dash_port = want
                self.M.log("info", "dashboard", f"Öffentliches Dashboard auf Port {want} (HTTP, nur lesen)")
            except OSError as e:
                self.M.log("error", "dashboard", f"Dashboard-Port {want} nicht verfügbar: {e}")

    def stop(self):
        self.stopping.set()
        for s in list(self.servers.values()):
            s.shutdown()
            s.server_close()

    # -------------------------------------------------------------- Helfer (Root-Aktionen)
    def helper_request(self, action, data):
        """Anfrage an fluidi-helper (root, systemd-Pfad-Unit) – der Dienst selbst hat keine Root-Rechte."""
        d = self.cfg.requests_path
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{int(time.time() * 1000)}-{action}.json"
        tmp = p.with_suffix(".tmp")
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump({"action": action, **data}, f)
        tmp.rename(p)

    def restart_later(self, s=3):
        def go():
            time.sleep(s)
            self.M.store.meta_set("last_stop", "restore")
            os._exit(3)  # systemd Restart=always startet neu, service.py spielt das Backup ein
        if not self.M.sim:
            threading.Thread(target=go, daemon=True).start()

    def fw_pubkey(self):
        p = self.cfg.fw_pubkey
        if not p or not Path(p).exists():
            return None
        return crypto.load_public_key(Path(p).read_bytes())

    def cert_info(self):
        try:
            return pki.info(self.cfg.tls_path)
        except Exception:  # noqa: BLE001
            return None

    def gateway_update(self, data: bytes) -> str:
        """Gateway-Update (REQ-GW-11): 'FLUIDIGW' · u16 Format 1 · u32 Länge · tar.gz · DER-Signatur (ECDSA P-256
        über SHA-256 aller Bytes davor). Auspacken nach data_dir/staging/<version>, Umschalten macht der Helfer
        (Symlink /opt/fluidi/current, Rückfall wenn der Dienst nicht startet)."""
        p = self.cfg.gw_update_pubkey
        if not p or not Path(p).exists():
            raise ApiError(422, "signature_invalid", "Kein Update-Schlüssel konfiguriert – Update wird nicht angenommen")
        if len(data) < 14 or data[:8] != b"FLUIDIGW":
            raise ApiError(400, "bad_request", "Kein fluidi-Gateway-Update")
        fmt, ln = struct.unpack_from("<HI", data, 8)
        body_end = 14 + ln
        if fmt != 1 or body_end > len(data):
            raise ApiError(400, "bad_request", "Update-Format")
        if not crypto.ecdsa_verify_digest(crypto.load_public_key(Path(p).read_bytes()), hashlib.sha256(data[:body_end]).digest(), data[body_end:]):
            self.M.log("warn", "gw_update", "Gateway-Update mit ungültiger Signatur abgelehnt")
            raise ApiError(422, "signature_invalid", "Signatur ungültig – Update verworfen")
        tar = tarfile.open(fileobj=io.BytesIO(data[14:body_end]), mode="r:gz")
        man = json.loads(tar.extractfile("manifest.json").read())
        ver = str(man["version"])
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", ver):
            raise ApiError(400, "bad_request", "Version im Manifest ungültig")
        dst = self.cfg.data_dir / "staging" / ver
        dst.mkdir(parents=True, exist_ok=True)
        for m in tar.getmembers():
            if m.name.startswith("/") or ".." in Path(m.name).parts or not (m.isfile() or m.isdir()):
                raise ApiError(400, "bad_request", f"Unzulässiger Pfad im Update: {m.name}")
        tar.extractall(dst, filter="data") if hasattr(tarfile, "data_filter") else tar.extractall(dst)  # noqa: S202
        self.helper_request("update", {"version": ver, "path": str(dst)})
        self.M.log("info", "gw_update", f"Gateway-Update {ver} geprüft, Umschaltung beauftragt")
        return ver
