"""Sesión 7 — pruebas de integración de la API (FastAPI TestClient, LLM falso)."""

import pytest
from conftest import POLITICA, respuesta_json
from fastapi.testclient import TestClient

from asistente.adapters.llm import providers
from asistente.api.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(providers._REGISTRY, "fake", lambda: providers.FakeLLM([respuesta_json()]))
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    with TestClient(app) as c:
        yield c


def _token(client, user, pwd):
    r = client.post("/v1/token", data={"username": user, "password": pwd})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_sin_token_es_401(client):
    assert client.post("/v1/ask", json={"question": "hola?"}).status_code == 401


def test_credenciales_invalidas(client):
    assert client.post("/v1/token", data={"username": "admin", "password": "x"}).status_code == 401


def test_analista_no_puede_cargar_documentos(client):
    h = _token(client, "analista", "analista123")
    r = client.post("/v1/documents", json={"title": "t", "content": "c"}, headers=h)
    assert r.status_code == 403


def test_conversacion_ajena_no_se_comparte(client):
    analista = _token(client, "analista", "analista123")
    admin = _token(client, "admin", "admin123")
    r = client.post("/v1/ask", json={"question": "¿vacaciones?"}, headers=analista)
    ajena = r.json()["conversation_id"]
    r2 = client.post(
        "/v1/ask", json={"question": "¿qué pregunté?", "conversation_id": ajena}, headers=admin
    )
    assert r2.status_code == 200
    assert r2.json()["conversation_id"] != ajena


def test_campos_desconocidos_y_tamano_maximo(client):
    admin = _token(client, "admin", "admin123")
    extra = {"title": "t", "content": "c", "owner": "otro"}
    assert client.post("/v1/documents", json=extra, headers=admin).status_code == 422
    enorme = {"title": "t", "content": "x" * 500_001}
    assert client.post("/v1/documents", json=enorme, headers=admin).status_code == 422


def _subir(client, headers, contenido, nombre="politica.md", tipo="text/markdown"):
    return client.post(
        "/v1/documents/archivo", files={"archivo": (nombre, contenido, tipo)}, headers=headers
    )


# taller: s06
def test_consultar_documento_y_404(client):
    admin = _token(client, "admin", "admin123")
    doc = client.post("/v1/documents", json={"title": "t", "content": POLITICA}, headers=admin)
    doc_id = doc.json()["id"]
    r = client.get(f"/v1/documents/{doc_id}", headers=admin)
    assert r.status_code == 200 and r.json()["title"] == "t"
    falta = client.get("/v1/documents/00000000-0000-0000-0000-000000000000", headers=admin)
    assert falta.status_code == 404 and "No existe" in falta.json()["detail"]


# taller: s07
def test_token_vencido_es_401(client, monkeypatch):
    from datetime import timedelta

    from asistente.api import security

    monkeypatch.setattr(security, "TTL", timedelta(seconds=-1))
    token = security.create_token("analista", ["docs:read"])
    r = client.post(
        "/v1/ask",
        json={"question": "¿vacaciones?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401
