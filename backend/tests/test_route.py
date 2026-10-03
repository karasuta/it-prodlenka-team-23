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
    assert data["groups"][0]["stops"][0]["name"] == "Красные рыбки (Золотые рыбки)"
    assert data["outro"] == FAKE_ROUTE["outro"]


def test_route_groups_stops_by_building(monkeypatch):
    monkeypatch.setattr(app.api.route, "settings", Settings(yandex_folder_id="test-folder"))
    # 4149 — здание 117 (Галерея), 3687 — здание 116 (Главное здание),
    # 4005 — здание 117 (Галерея). AI вернул их «вперемешку».
    route_with_two_buildings = {
        "intro": "Привет!",
        "route": [
            {"id": "4149", "name": "Красные рыбки (Золотые рыбки)", "why": "Яркая.", "story": "Аквариум.", "fun_fact": "", "quest": ""},
            {"id": "3687", "name": "Портрет юноши в золотом венке", "why": "Фаюмский портрет.", "story": "Древний портрет.", "fun_fact": "", "quest": ""},
            {"id": "4005", "name": "Нападение ягуара на лошадь", "why": "Джунгли.", "story": "Руссо.", "fun_fact": "", "quest": ""},
        ],
        "outro": "Конец!",
    }
    monkeypatch.setattr(
        app.api.route,
        "ask",
        lambda prompt, instructions, timeout: json.dumps(route_with_two_buildings, ensure_ascii=False),
    )

    with TestClient(fastapi_app) as client:
        response = client.post("/api/route", json={"audience": "новичок"})

    assert response.status_code == 200
    groups = response.json()["groups"]
    # Группы идут в порядке первого появления здания: 117 (Галерея), затем 116 (Главное здание).
    assert [group["building"] for group in groups] == [
        "Галерея искусства стран Европы и Америки XIX–XX веков",
        "Главное здание",
    ]
    assert [stop["id"] for stop in groups[0]["stops"]] == ["4149", "4005"]
    assert [stop["id"] for stop in groups[1]["stops"]] == ["3687"]
    # Здание 116 в локации отображается человекочитаемым названием.
    assert "Главное здание" in groups[1]["stops"][0]["location"]
    # Внутренний id зала 191 переводится в реальный номер «Зал 16».
    assert "Зал 16" in groups[1]["stops"][0]["location"]
    assert "Зал 191" not in groups[1]["stops"][0]["location"]


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
    stop = response.json()["groups"][0]["stops"][0]
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
    assert response.json()["groups"][0]["stops"][0]["id"] == "4149"


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