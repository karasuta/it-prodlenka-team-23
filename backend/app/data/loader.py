"""Загрузка датасета шедевров Пушкинского музея.

Файл `masterpieces.json` — это словарь: ключ — строковый id экспоната,
значение — объект с полями name, authors, period, type, material, text и т.д.

Мы нормализуем его в список простых объектов, которые удобно отдавать
на фронтенд и подставлять в промпт AI Studio.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent
MASTERPIECES_PATH = DATA_DIR / "masterpieces.json"


class Masterpiece:
    """Нормализованный экспонат. Все поля опциональны: в датасете они часто пустые."""

    __slots__ = ("id", "name", "author", "period", "type_", "country", "material", "size", "hall", "building", "text", "images")

    def __init__(self, raw: dict[str, Any], object_id: str) -> None:
        self.id = object_id
        self.name = _ru(raw.get("name")) or "Без названия"
        self.author = _author(raw)
        self.period = _ru(raw.get("period", {}).get("name") if isinstance(raw.get("period"), dict) else None) or ""
        self.type_ = _ru(raw.get("type")) or ""
        self.country = _ru(raw.get("country")) or ""
        self.material = _ru(raw.get("material")) or ""
        self.size = _ru(raw.get("size")) or ""
        self.hall = str(raw.get("hall") or "")
        self.building = str(raw.get("building") or "")
        self.text = _ru(raw.get("text")) or ""
        self.images = _images(raw)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "period": self.period,
            "type": self.type_,
            "country": self.country,
            "material": self.material,
            "size": self.size,
            "hall": self.hall,
            "building": self.building,
            "text": self.text,
            "images": self.images,
        }


def _ru(value: Any) -> str:
    """Достаём русский текст из значения вида {'ru': '...', 'en': '...'} или строки."""
    if isinstance(value, dict):
        return str(value.get("ru") or value.get("en") or "")
    return str(value or "")


def _author(raw: dict[str, Any]) -> str:
    authors = raw.get("authors")
    if not isinstance(authors, dict):
        return ""
    names = [_ru(item.get("name")) for item in authors.values() if isinstance(item, dict)]
    return ", ".join(name for name in names if name)


def _images(raw: dict[str, Any]) -> list[str]:
    gallery = raw.get("gallery")
    if not isinstance(gallery, dict):
        return []
    paths: list[str] = []
    for item in gallery.values():
        if not isinstance(item, dict):
            continue
        # В датасете несколько ракурсов; берём первый доступный.
        for key in ("id01", "id02", "id03"):
            path = item.get(key)
            if path:
                paths.append(str(path))
                break
    return paths


@lru_cache(maxsize=1)
def load_masterpieces() -> list[Masterpiece]:
    """Читает датасет один раз и возвращает список экспонатов."""
    with MASTERPIECES_PATH.open(encoding="utf-8") as fh:
        raw_by_id: dict[str, Any] = json.load(fh)
    return [Masterpiece(raw, object_id) for object_id, raw in raw_by_id.items()]


def get_masterpieces_with_images() -> list[Masterpiece]:
    """Экспонаты, у которых есть хотя бы одна картинка (для маршрута новичка)."""
    return [item for item in load_masterpieces() if item.images]