"""Эндпоинт персонального маршрута: «Искусствовед-переводчик».

Пользователь присылает параметры (аудитория, время, интересы), а бэкенд:
1. берёт из датасета экспонаты с изображениями (кандидаты в маршрут);
2. отправляет их в AI Studio вместе с ролью и правилами агента;
3. получает JSON с маршрутом и возвращает его фронтенду.

AI Studio вызывается только здесь, на бэкенде: ключи не попадают во фронтенд.
"""

import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai import ask
from app.config import settings
from app.data.loader import get_masterpieces_with_images

logger = logging.getLogger("app.api.route")

router = APIRouter(tags=["route"])

MAX_CANDIDATES = 30


class RouteRequest(BaseModel):
    audience: str = Field(description="Целевая аудитория: новичок, родители с детьми, турист, студент, знаток")
    time_minutes: int | None = Field(default=None, ge=10, le=480, description="Сколько минут есть у посетителя")
    interests: str = Field(default="", description="Что интересно: истории о людях, красивые вещи, необычное")


class RouteStop(BaseModel):
    id: str
    name: str
    author: str
    location: str = ""
    why: str
    story: str
    fun_fact: str
    quest: str
    image: str = ""


class RouteResponse(BaseModel):
    intro: str
    route: list[RouteStop]
    outro: str


AGENT_INSTRUCTIONS = """Ты — «Искусствовед-переводчик»: персональный гид по Пушкинскому музею для человека, который не разбирается в искусстве.

Правила:
1. Никакого снобизма: жаргон объясняй простыми словами или аналогиями.
2. Эмпатия к новичку: начинай с того, что видно глазами, потом контекст.
3. Используй ТОЛЬКО экспонаты из предоставленного списка, не выдумывай названия, авторов и залы.
4. Для каждого объекта объясни, почему он попал в маршрут именно для этой аудитории.
5. Не перегружай: 5-7 объектов, короткие рассказы.
6. Адаптируйся под аудиторию: детям — квесты «найди на картине», туристу — хиты и порядок обхода, студенту — связь с современностью, знатоку — редкие детали.
7. Отвечай на русском, живым и тёплым тоном.
8. Не начинай каждый рассказ с «На этой картине...» — используй разные формулировки: «Здесь», «В центре внимания», «Смотрите», «Этот экспонат» и т.п.

Ответ — строго JSON без markdown-обёртки:
{
  "intro": "Приветствие на 1-2 предложения, снимающее страх новичка",
  "route": [
    {
      "id": "числовой id из списка",
      "name": "Название",
      "author": "Автор или 'Неизвестный мастер'",
      "why": "почему объект в маршруте для этой аудитории",
      "story": "рассказ для новичка: что вижу, почему круто, деталь (3-5 предложений)",
      "fun_fact": "одна короткая зацепка-ассоциация",
      "quest": "мини-задание «найди на экспонате...» (пустая строка, если не подходит)"
    }
  ],
  "outro": "Итог: как менялось искусство по маршруту, что запомнить (1-2 предложения)"
}"""


def _build_prompt(request: RouteRequest, candidates: list[dict]) -> str:
    time_line = f"Время: {request.time_minutes} минут." if request.time_minutes else "Время: не указано."
    interests_line = f"Интересы: {request.interests}." if request.interests else "Интересы: не указаны."
    return (
        f"Аудитория: {request.audience}.\n"
        f"{time_line}\n"
        f"{interests_line}\n\n"
        "Доступные экспонаты (id, название, автор, зал, здание, техника):\n"
        + "\n".join(
            f"- {item['id']}: {item['name']} | {item['author'] or 'Неизвестный мастер'} | "
            f"зал {item['hall'] or '?'} | здание {item['building'] or '?'} | {item['type'] or '?'}"
            for item in candidates
        )
    )


def _location_from_candidate(candidate: dict) -> str:
    """Человекочитаемая локация экспоната из данных датасета.

    В датасете хранятся номер зала (`hall`) и номер здания (`building`).
    У части экспонатов зал пустой — тогда показываем хотя бы здание.
    """
    parts: list[str] = []
    if candidate.get("hall"):
        parts.append(f"Зал {candidate['hall']}")
    if candidate.get("building"):
        parts.append(f"Здание {candidate['building']}")
    return ", ".join(parts)


def _parse_route(raw_answer: str, candidates: dict[str, dict]) -> RouteResponse:
    text = raw_answer.strip()
    # Модель может обернуть JSON в ```json ... ``` — снимаем обёртку.
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("AI returned invalid JSON: %s", exc)
        raise HTTPException(status_code=502, detail="AI вернул некорректный ответ") from exc

    stops: list[RouteStop] = []
    for stop in payload.get("route", []):
        stop_id = str(stop.get("id", ""))
        candidate = candidates.get(stop_id, {})
        # Исключаем объекты без фото: в маршруте остаются только экспонаты с изображением.
        if not candidate.get("images"):
            continue
        stops.append(
            RouteStop(
                id=stop_id,
                name=str(stop.get("name") or candidate.get("name") or "Без названия"),
                author=str(stop.get("author") or candidate.get("author") or "Неизвестный мастер"),
                location=_location_from_candidate(candidate),
                why=str(stop.get("why", "")),
                story=str(stop.get("story", "")),
                fun_fact=str(stop.get("fun_fact", "")),
                quest=str(stop.get("quest", "")),
                image=candidate.get("images", [""])[0] if candidate.get("images") else "",
            )
        )
    return RouteResponse(
        intro=str(payload.get("intro", "")),
        route=stops,
        outro=str(payload.get("outro", "")),
    )


@router.post("/route", response_model=RouteResponse)
def build_route(request: RouteRequest) -> RouteResponse:
    if not settings.yandex_folder_id:
        raise HTTPException(status_code=503, detail="AI Studio is not configured: set YANDEX_FOLDER_ID")

    candidates = [item.to_dict() for item in get_masterpieces_with_images()][:MAX_CANDIDATES]
    if not candidates:
        raise HTTPException(status_code=503, detail="No masterpieces data available")

    prompt = _build_prompt(request, candidates)
    try:
        answer = ask(prompt, instructions=AGENT_INSTRUCTIONS, timeout=50)
    except Exception as exc:  # noqa: BLE001 - any AI Studio failure is a bad gateway
        logger.warning("AI Studio call failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI Studio call failed ({type(exc).__name__})") from exc

    return _parse_route(answer, {item["id"]: item for item in candidates})