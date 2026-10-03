"""Тесты эндпоинта /api/route («Искусствовед-переводчик»)."""

import json

from fastapi.testclient import TestClient

import app.api.route
from app.config import Settings
from app.main import app as fastapi_app

FAKE_ROUTE = {
    "intro": "Привет! Сейчас покажу, с чего начать.",
    "route": [
        {
            "id": "4149",
            "name": "Красные рыбки (Золотые рыбки)",
            "author": "Анри Матисс",
            "why": "Самая узнаваемая и яркая картина, её легко найти.",
            "story": "Большой аквариум с красными рыбками в центре. Матисс хотел передать движение и радость цвета.",
            "fun_fact": "Картину купил коллекционер Щукин прямо из мастерской художника.",
            "quest": "Найди на картине, сколько рыбок плавает в аквариуме.",
        }
    ],
    "outro": "Вы прошли путь от Древнего Египта до XX века!",
}


def test_route_returns_route(monkeypatch):
    monkeypatch.setattr(app.api.route, "settings", Settings(yandex_folder_id="test-folder"))
    monkeypatch.setattr(
        app.api.route,
        "ask",
        lambda prompt, instructions, timeout: json.dumps(FAKE_ROUTE, ensure_ascii=False),
    )

    with TestClient(fastapi_app) as client:
        response = client.post("/api/route", json={"audience": "новичок", "time_minutes": 60})

    assert response.status_code == 200
    data = response.json()
    assert data["intro"] == FAKE_ROUTE["intro"]
    assert data["route"][0]["name"] == "Красные рыбки (Золотые рыбки)"
    assert data["outro"] == FAKE_ROUTE["outro"]


def test_route_injects_image_from_dataset(monkeypatch):
    monkeypatch.setattr(app.api.route, "settings", Settings(yandex_folder_id="test-folder"))
    monkeypatch.setattr(
        app.api.route,
        "ask",
        lambda prompt, instructions, timeout: json.dumps(FAKE_ROUTE, ensure_ascii=False),
    )

    with TestClient(fastapi_app) as client:
        response = client.post("/api/route", json={"audience": "новичок"})

    assert response.status_code == 200
    stop = response.json()["route"][0]
    # Модель не присылала картинку — бэкенд берёт путь из датасета по id экспоната.
    assert stop["id"] == "4149"
    assert stop["image"].startswith("/data/fonds/")
    assert stop["image"].endswith(".jpg")


def test_route_strips_markdown_fence(monkeypatch):
    monkeypatch.setattr(app.api.route, "settings", Settings(yandex_folder_id="test-folder"))
    wrapped = "```json\n" + json.dumps(FAKE_ROUTE, ensure_ascii=False) + "\n```"

    def fake_ask(prompt, instructions, timeout):
        return wrapped

    monkeypatch.setattr(app.api.route, "ask", fake_ask)

    with TestClient(fastapi_app) as client:
        response = client.post("/api/route", json={"audience": "новичок"})

    assert response.status_code == 200
    assert response.json()["route"][0]["id"] == "4149"


def test_route_returns_503_when_not_configured(monkeypatch):
    monkeypatch.setattr(app.api.route, "settings", Settings(yandex_folder_id=""))

    with TestClient(fastapi_app) as client:
        response = client.post("/api/route", json={"audience": "новичок"})

    assert response.status_code == 503


def test_route_returns_502_when_model_fails(monkeypatch):
    monkeypatch.setattr(app.api.route, "settings", Settings(yandex_folder_id="test-folder"))

    def failing_ask(prompt, instructions, timeout):
        raise RuntimeError("boom")

    monkeypatch.setattr(app.api.route, "ask", failing_ask)

    with TestClient(fastapi_app) as client:
        response = client.post("/api/route", json={"audience": "новичок"})

    assert response.status_code == 502


def test_route_returns_502_on_invalid_json(monkeypatch):
    monkeypatch.setattr(app.api.route, "settings", Settings(yandex_folder_id="test-folder"))
    monkeypatch.setattr(app.api.route, "ask", lambda prompt, instructions, timeout: "not json at all")

    with TestClient(fastapi_app) as client:
        response = client.post("/api/route", json={"audience": "новичок"})

    assert response.status_code == 502


def test_route_validates_time_minutes(monkeypatch):
    with TestClient(fastapi_app) as client:
        response = client.post("/api/route", json={"audience": "новичок", "time_minutes": 5})

    assert response.status_code == 422