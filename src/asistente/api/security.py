"""Sesiones 7 y 13: OAuth2 password flow + JWT con permisos (scopes) y grupos (versión didáctica).

En producción: usuarios en BD o proveedor de identidad, hash con argon2 (pwdlib), SECRET desde
un gestor de secretos, tokens de corta duración + refresh, límite de intentos, HTTPS obligatorio.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

log = logging.getLogger(__name__)

# Sin JWT_SECRET no hay clave por defecto conocida (con ella cualquiera falsificaría tokens):
# se genera una aleatoria por proceso y los tokens dejan de valer al reiniciar.
SECRET = os.getenv("JWT_SECRET") or secrets.token_urlsafe(32)
if not os.getenv("JWT_SECRET"):
    log.warning("JWT_SECRET no está definida: se usa una clave temporal")
ALGORITHM = "HS256"
TTL = timedelta(minutes=30)
_ITERATIONS = 600_000

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/token")


def hash_password(password: str, salt: bytes | None = None) -> str:
    """'sal$hash' en hexadecimal. Una sal aleatoria por usuario evita reconocer claves iguales."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, _, _ = stored.partition("$")
    return hmac.compare_digest(stored, hash_password(password, bytes.fromhex(salt_hex)))


# Usuarios de demostración: usuario → (hash, scopes, grupos). Grupos: qué documentos puede ver.
USERS: dict[str, tuple[str, list[str], list[str]]] = {
    "analista": (hash_password("analista123"), ["docs:read", "solicitudes:crear"], ["todos"]),
    "admin": (
        hash_password("admin123"),
        ["docs:read", "docs:write", "solicitudes:crear"],
        ["todos", "rrhh"],
    ),
}
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def authenticate(username: str, password: str) -> tuple[list[str], list[str]] | None:
    """(scopes, grupos) si las credenciales son correctas; None si no."""
    user = USERS.get(username)
    # Si el usuario no existe se verifica igual contra un hash ficticio: la respuesta tarda
    # lo mismo y no revela qué usuarios existen.
    ok = verify_password(password, user[0] if user else _DUMMY_HASH)
    return (user[1], user[2]) if user and ok else None


def create_token(sub: str, scopes: list[str], groups: list[str] | None = None) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": sub,
        "scopes": scopes,
        "groups": groups or ["todos"],
        "iat": now,
        "exp": now + TTL,
    }
    return jwt.encode(claims, SECRET, algorithm=ALGORITHM)


def groups_of(user: dict[str, object]) -> frozenset[str]:
    """Los grupos del token; sin grupos, solo lo público."""
    grupos = user.get("groups")
    return frozenset(str(g) for g in grupos) if isinstance(grupos, list) else frozenset({"todos"})


def current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, object]:
    try:
        claims = jwt.decode(
            token, SECRET, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]}
        )
        return dict(claims)
    except jwt.PyJWTError as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token inválido o vencido",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def require_scope(scope: str) -> Callable[..., dict[str, object]]:
    def checker(user: Annotated[dict[str, object], Depends(current_user)]) -> dict[str, object]:
        if scope not in (user.get("scopes") or []):  # type: ignore[operator]
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Falta el permiso {scope}")
        return user

    return checker
