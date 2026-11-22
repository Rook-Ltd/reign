"""BasicAuthProvider — username/password dashboard auth (no OAuth IDP).

Login is a credential form (``supports_password`` + ``complete_password_login``); cookies,
verify, refresh, ws-tickets and logout are the shared framework. Sessions are stateless
HMAC-signed tokens (no IDP, no database) whose key is derived from the signing secret AND the
configured credential, so changing the username or password ends every session; logout records
the login's session id in ``dashboard_auth/basic-revoked-sessions.json`` under the Reign home,
which every renewal of that login carries, so a copied token of it stops working too. Passwords use stdlib scrypt and login always hashes
even for an unknown username (no username-enumeration timing oracle). Config: ``dashboard.
basic_auth.{username,password_hash|password,users,secret,session_ttl_seconds}`` or the
``REIGN_DASHBOARD_BASIC_AUTH_*`` env vars (env wins when non-empty; see ``_settings``). ``users`` maps
extra usernames to password hashes (managed by ``reign dashboard users``); a session is only
valid while its user is still configured, so removing a user locks them out on the next request.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Mapping, Optional

from reign_cli.dashboard_auth import DashboardAuthProvider, InvalidCredentialsError, RefreshExpiredError, Session
from reign_constants import get_reign_home
from plugins.dashboard_auth._shared import (
    NonInteractiveMixin, SkipRegistration, load_config_section, register_provider, resolve_env_or_cfg)
from utils import atomic_json_write, read_json_or_empty

logger = logging.getLogger(__name__)
_TAG = "dashboard-auth-basic"

# The middleware transparently refreshes via the 30-day refresh token when the
# access token lapses, so the TTL controls refresh frequency, not login length.
_DEFAULT_TTL_SECONDS = 12 * 60 * 60
_REFRESH_TTL_SECONDS = 30 * 24 * 60 * 60

# Interactive-login scrypt parameters (~16 MiB, a few ms); n must be a power of two.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32
_SCRYPT_SALT_BYTES = 16

# HMAC-SHA256 digest is appended to signed tokens as a fixed-length suffix
# (no separator — binary HMAC bytes can't be confused with a delimiter).
_SIG_LEN = hashlib.sha256().digest_size

_REVOKED_PATH = Path("dashboard_auth") / "basic-revoked-sessions.json"

LAST_SKIP_REASON: str = ""


# ---- Password hashing (stdlib scrypt) ----

def hash_password(password: str) -> str:
    """Return a ``scrypt$n$r$p$<salt_b64>$<dk_b64>`` hash string. Public so operators can
    precompute ``password_hash`` for config.yaml (the plaintext then never sits at rest):
    ``python -c "from plugins.dashboard_auth.basic import hash_password; print(hash_password('pw'))"``."""
    salt = secrets.token_bytes(_SCRYPT_SALT_BYTES)
    dk = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_SCRYPT_DKLEN, maxmem=0)
    salt_b64, dk_b64 = base64.b64encode(salt).decode(), base64.b64encode(dk).decode()
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt_b64}${dk_b64}"


def _verify_password(password: str, encoded: str) -> bool:
    """Constant-time scrypt verify. False on any malformed hash string."""
    try:
        scheme, n_s, r_s, p_s, salt_b64, dk_b64 = encoded.split("$")
        if scheme != "scrypt":
            return False
        n, r, p = int(n_s), int(r_s), int(p_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
    except (ValueError, TypeError):
        return False
    try:
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=len(expected), maxmem=0)
    except (ValueError, MemoryError):
        return False
    return hmac.compare_digest(actual, expected)


# Verified against when the username is unknown so "no such user" and "wrong
# password" take comparable time.
_DUMMY_HASH = hash_password("dummy-password-for-constant-time-verify")


# ---- Token signing (stateless HMAC-signed blobs) ----

def _sign(payload: dict, secret: bytes) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    sig = hmac.new(secret, raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + sig).decode()


def _unsign(token: str, secret: bytes, kind: str) -> Optional[dict]:
    """Return the payload if the signature is valid, ``kind`` matches and it
    is unexpired; ``None`` otherwise (including on any decode error)."""
    try:
        blob = base64.urlsafe_b64decode(token.encode())
        if len(blob) <= _SIG_LEN:
            return None
        raw, sig = blob[:-_SIG_LEN], blob[-_SIG_LEN:]
        expected = hmac.new(secret, raw, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(raw)
    except Exception:
        return None
    if payload.get("kind") != kind or payload.get("exp", 0) <= int(time.time()):
        return None
    return payload


# ---- Provider ----

class BasicAuthProvider(NonInteractiveMixin, DashboardAuthProvider):
    """Username/password provider with stateless HMAC-signed sessions."""

    name = "basic"
    display_name = "Username & Password"
    supports_password = True
    # Used refresh tokens stay valid (stateless, no reuse detection), so the gate's replay cache
    # would only let a cached rotation outlive a logout: every replay goes to the sid check.
    refresh_reuse_detection = False
    _NOT_INTERACTIVE = "BasicAuthProvider is password-only; use complete_password_login."
    _NO_START_LOGIN = (
        "BasicAuthProvider is password-only; there is no OAuth redirect flow. "
        "The login page POSTs to /auth/password-login instead.")

    def __init__(self, *, users: Mapping[str, str], secret: bytes, ttl_seconds: int = _DEFAULT_TTL_SECONDS,
                 credential_ids: Optional[Mapping[str, str]] = None) -> None:
        """*credential_ids* maps a username to a restart-stable form of its credential (the
        configured plaintext when its ``password_hash`` was hashed in-memory with a random salt);
        a user without one is bound to its ``password_hash``. Each user's tokens are signed with a
        key derived from that user's credential, so changing or removing one user's password ends
        that user's sessions, and only theirs, even when ``secret`` stays the same."""
        if not users:
            raise ValueError("users must contain at least one username")
        for username, password_hash in users.items():
            if not username:
                raise ValueError("username must be non-empty")
            if not password_hash:
                raise ValueError(f"password_hash for {username!r} must be non-empty")
        if len(secret) < 16:
            raise ValueError("secret must be at least 16 bytes")
        self._users = dict(users)
        ids = dict(credential_ids or {})
        self._keys = {
            username: hmac.new(secret, b"\0".join((b"reign-dashboard-basic-session", username.encode(),
                                                    (ids.get(username) or password_hash).encode())),
                               hashlib.sha256).digest()
            for username, password_hash in self._users.items()}
        self._ttl = max(60, int(ttl_seconds))
        self._revoked_path = get_reign_home() / _REVOKED_PATH
        self._revoked: dict[str, int] = {}

    # ---- password login ----------------------------------------------------

    def complete_password_login(self, *, username: str, password: str) -> Session:
        # Always run a scrypt verify (the dummy hash for an unknown username) so "no such
        # user" and "wrong password" take comparable time.
        password_hash = self._users.get(username)
        password_ok = _verify_password(password, password_hash or _DUMMY_HASH)
        if password_hash is None or not password_ok:
            raise InvalidCredentialsError("invalid username or password")
        return self._mint_session(username)

    # ---- session lifecycle -------------------------------------------------

    def verify_session(self, *, access_token: str) -> Optional[Session]:
        payload = self._unsign(access_token, "access")
        if payload is None or self._is_revoked(payload):
            return None
        return self._session(str(payload.get("sub", "")), int(payload["exp"]), access_token, "")

    def refresh_session(self, *, refresh_token: str) -> Session:
        if not refresh_token:
            raise RefreshExpiredError("no refresh token present in session")
        payload = self._unsign(refresh_token, "refresh")
        if payload is None or self._is_revoked(payload):
            raise RefreshExpiredError("refresh token expired or invalid")
        return self._mint_session(str(payload["sub"]), str(payload["sid"]))

    def revoke_session(self, *, refresh_token: str) -> None:
        # Ends this login and every token renewed from it (they share its ``sid``); other logins
        # stay. Must not raise: a failed write still revokes in this process.
        self._revoke(self._unsign(refresh_token, "refresh") if refresh_token else None)

    def revoke_access_session(self, *, access_token: str) -> None:
        # With ``session_ttl_seconds`` above the refresh TTL, the access token is all a late logout has.
        self._revoke(self._unsign(access_token, "access") if access_token else None)

    # ---- internals ---------------------------------------------------------

    def _revoke(self, payload: Optional[dict]) -> None:
        if payload is None or not payload.get("sid"):
            return
        now = int(time.time())
        self._load_revoked()
        # Any token of this login was minted before now, so none outlives now + its longest TTL
        # (``session_ttl_seconds`` may exceed the refresh TTL).
        self._revoked = {sid: exp for sid, exp in self._revoked.items() if exp > now}
        self._revoked[str(payload["sid"])] = now + max(self._ttl, _REFRESH_TTL_SECONDS)
        try:
            atomic_json_write(self._revoked_path, self._revoked, mode=0o600)
        except OSError as exc:
            logger.warning("dashboard-auth-basic: could not persist the revoked session (%s); "
                           "it stays revoked until this process exits", exc)

    def _load_revoked(self) -> None:
        """Merge the revocation file (another process sharing the secret, or this one before a
        restart, may have written it). Read every time: a replacement can keep the old mtime on a
        coarse-timestamp filesystem, and skipping it would also let this process's next write drop
        that revocation. The file only holds unexpired logouts, so the read is small."""
        stored = read_json_or_empty(self._revoked_path)
        self._revoked.update({str(k): v for k, v in stored.items() if isinstance(v, int)})

    def _is_revoked(self, payload: dict) -> bool:
        sid = payload.get("sid")
        if not sid:
            return True
        self._load_revoked()
        return self._revoked.get(str(sid), 0) > int(time.time())

    def _unsign(self, token: str, kind: str) -> Optional[dict]:
        """``_unsign`` with the key of the user the token names; ``None`` for a user not (or no
        longer) configured."""
        try:
            sub = json.loads(base64.urlsafe_b64decode(token.encode())[:-_SIG_LEN]).get("sub")
        except Exception:
            return None
        key = self._keys.get(sub) if isinstance(sub, str) else None
        return _unsign(token, key, kind) if key else None

    def _mint_session(self, user_id: str, sid: str = "") -> Session:
        # ``jti`` gives every session its own tokens, even two minted in one second: a listener that
        # drops a session's tokens (the Webapp's sign-out) must not get them back from a later login.
        # ``sid`` names the login and survives renewals, so logout can revoke the whole chain.
        now = int(time.time())
        exp = now + self._ttl
        jti = secrets.token_urlsafe(16)
        sid = sid or secrets.token_urlsafe(16)
        claims = {"sub": user_id, "jti": jti, "sid": sid}
        key = self._keys[user_id]
        return self._session(
            user_id, exp,
            _sign({**claims, "kind": "access", "exp": exp}, key),
            _sign({**claims, "kind": "refresh", "exp": now + _REFRESH_TTL_SECONDS}, key))

    def _session(self, user_id: str, exp: int, access_token: str, refresh_token: str) -> Session:
        return Session(
            user_id=user_id, email="", display_name=user_id, org_id="", provider=self.name,
            expires_at=exp, access_token=access_token, refresh_token=refresh_token)


# ---- Plugin entry point ----

def _load_config_basic_auth_section() -> dict:
    return load_config_section(logger, _TAG, "dashboard", "basic_auth")


# Shell syntax that was written to .env/config without being run, e.g. a
# ``$(openssl rand -base64 32)`` line inside a quoted heredoc, or the command (or a doc
# placeholder naming it) pasted in place of its output. Base64 and hex never contain
# these (nor a space), and everyone who copied the same line would share the same key.
_UNEXPANDED_SHELL_MARKERS = ("$(", "`", "openssl rand")

# The error above only reaches the log files, not the console of ``reign serve`` /
# ``reign dashboard``; one stderr line per process makes it visible there too.
_shell_text_secret_reported = False


def _resolve_secret(cfg_section: dict) -> bytes:
    """Resolve the token-signing secret (base64, hex, or raw text). When unset, generates
    a random per-process secret (sessions then don't survive a restart or span multiple
    workers — logged at INFO). A value holding unexpanded shell text is never used as the
    key: it is logged as an error and replaced by a random per-process secret."""
    raw = resolve_env_or_cfg("REIGN_DASHBOARD_BASIC_AUTH_SECRET", cfg_section.get("secret"))
    if not raw:
        logger.info(
            "dashboard-auth-basic: no 'secret' configured; generating a random "
            "per-process signing key. Sessions will not survive a restart or span "
            "multiple workers. Set dashboard.basic_auth.secret (or "
            "REIGN_DASHBOARD_BASIC_AUTH_SECRET) for stable sessions.")
        return secrets.token_bytes(32)
    if any(marker in raw for marker in _UNEXPANDED_SHELL_MARKERS):
        logger.error(
            "dashboard-auth-basic: the configured signing secret contains unexpanded shell "
            "text (such as '$(openssl rand -base64 32)') instead of a random value, so it "
            "is ignored and a random per-process signing key is used. Set "
            "REIGN_DASHBOARD_BASIC_AUTH_SECRET (or dashboard.basic_auth.secret) to the "
            "output of 'openssl rand -base64 32' to keep sessions across restarts.")
        global _shell_text_secret_reported
        if not _shell_text_secret_reported:
            _shell_text_secret_reported = True
            print(
                "reign: dashboard login: REIGN_DASHBOARD_BASIC_AUTH_SECRET (or "
                "dashboard.basic_auth.secret) holds shell text instead of a random value; "
                "using a per-process key, so sessions end on restart. Replace it with the "
                "output of: openssl rand -base64 32", file=sys.stderr, flush=True)
        return secrets.token_bytes(32)
    for decoder in (base64.b64decode, bytes.fromhex):
        try:
            decoded = decoder(raw)
            if len(decoded) >= 16:
                return decoded
        except (ValueError, TypeError):
            pass
    return raw.encode("utf-8")


def _config_users(section: dict) -> dict:
    """``dashboard.basic_auth.users`` as ``{username: password_hash}``, dropping blank entries."""
    raw = section.get("users") or {}
    if not isinstance(raw, dict):
        logger.warning("dashboard-auth-basic: dashboard.basic_auth.users must be a mapping; ignoring it.")
        return {}
    return {str(name).strip(): str(h).strip() for name, h in raw.items() if str(name).strip() and str(h or "").strip()}


def _settings() -> dict:
    """Resolve BasicAuthProvider kwargs from env/config; raises ``SkipRegistration``."""
    section = _load_config_basic_auth_section()

    def setting(env_name: str, cfg_key: str) -> str:
        return resolve_env_or_cfg(env_name, section.get(cfg_key, ""))

    users = _config_users(section)
    username = setting("REIGN_DASHBOARD_BASIC_AUTH_USERNAME", "username")
    password_hash = setting("REIGN_DASHBOARD_BASIC_AUTH_PASSWORD_HASH", "password_hash")
    plaintext = setting("REIGN_DASHBOARD_BASIC_AUTH_PASSWORD", "password")
    ttl_raw = setting("REIGN_DASHBOARD_BASIC_AUTH_TTL_SECONDS", "session_ttl_seconds")
    if not username and not users:
        raise SkipRegistration(
            "dashboard.basic_auth.username is not set (and REIGN_DASHBOARD_BASIC_AUTH_USERNAME "
            "is empty), and dashboard.basic_auth.users is empty. Set a username and a password "
            "(or password_hash) under dashboard.basic_auth in config.yaml, or add users with "
            "`reign dashboard users add`, to enable username/password dashboard login, or use "
            "the OAuth provider, or pass --insecure to skip the auth gate.")
    if username and not password_hash and not plaintext:
        raise SkipRegistration(
            "dashboard.basic_auth.username is set but neither password_hash nor password "
            "is configured. Provide one of them (password_hash is preferred — compute it "
            "with plugins.dashboard_auth.basic.hash_password).",
            level="warning")
    # Precedence: env password (hashed in-memory) overrides any config password_hash so
    # operators can rotate without editing config; a config password_hash wins over a
    # config-only plaintext password (preferred at-rest form).
    credential_ids = {}
    if username:
        plaintext_from_env = os.environ.get("REIGN_DASHBOARD_BASIC_AUTH_PASSWORD", "").strip()
        # The in-memory hash of a plaintext password is salted afresh each start; the plaintext is
        # the stable form that binds sessions to the credential (see BasicAuthProvider.__init__).
        credential_id = plaintext_from_env or (plaintext if not password_hash else "")
        if plaintext_from_env:
            password_hash = hash_password(plaintext_from_env)
            logger.info("dashboard-auth-basic: hashed env-supplied password in-memory (overrides any config password_hash).")
        elif not password_hash:
            password_hash = hash_password(plaintext)
            logger.info(
                "dashboard-auth-basic: hashed plaintext password in-memory. "
                "For production, precompute dashboard.basic_auth.password_hash "
                "and remove the plaintext password from config.")
        # The primary username's credentials win over a same-named users entry.
        users[username] = password_hash
        if credential_id:
            credential_ids[username] = credential_id
    try:
        ttl = int(ttl_raw) if ttl_raw else _DEFAULT_TTL_SECONDS
    except ValueError:
        ttl = _DEFAULT_TTL_SECONDS
    return {"users": users, "secret": _resolve_secret(section), "ttl_seconds": ttl, "credential_ids": credential_ids}


def register(ctx) -> None:
    """Register ``BasicAuthProvider`` when username + (password or
    password_hash) are configured; a no-op for OAuth / ``--insecure`` setups."""
    global LAST_SKIP_REASON
    LAST_SKIP_REASON = ""
    kwargs, LAST_SKIP_REASON = register_provider(ctx, logger, _TAG, BasicAuthProvider, _settings)
    if kwargs is not None:
        logger.info("dashboard-auth-basic: registered password provider (users=%s)", ", ".join(sorted(kwargs["users"])))
