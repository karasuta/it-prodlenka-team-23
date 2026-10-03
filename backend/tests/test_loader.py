"""Тесты загрузчика датасета шедевров (backend/app/data/loader.py)."""

from app.data.loader import _images, _ru, get_masterpieces_with_images, load_masterpieces


def test_load_masterpieces_returns_objects():
    items = load_masterpieces()
    assert len(items) > 0
    item = items[0]
    assert item.id
    assert item.name
    assert hasattr(item, "images")


def test_get_masterpieces_with_images_filters():
    all_items = load_masterpieces()
    with_images = get_masterpieces_with_images()
    assert len(with_images) > 0
    assert all(item.images for item in with_images)
    assert len(with_images) <= len(all_items)


def test_ru_extracts_russian_from_dict():
    assert _ru({"ru": "Привет", "en": "Hello"}) == "Привет"
    assert _ru("Просто строка") == "Просто строка"
    assert _ru(None) == ""


def test_images_reads_first_gallery_view():
    raw = {
        "gallery": {
            "1": {"id01": "/data/fonds/a/1.jpg", "id02": "/data/fonds/a/2.jpg"},
            "2": {"id03": "/data/fonds/b/3.jpg"},
        }
    }
    paths = _images(raw)
    assert paths == ["/data/fonds/a/1.jpg", "/data/fonds/b/3.jpg"]

    assert _images({}) == []
    assert _images({"gallery": "not-a-dict"}) == []