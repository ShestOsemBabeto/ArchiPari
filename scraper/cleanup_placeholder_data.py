"""
cleanup_placeholder_data.py
----------------------------
Премахва останалите демонстрационни/фиктивни оферти от
data/products.json — тези с placehold.co снимки или измислени
"/produkt-demo" линкове (останали от първоначалния примерен сайт).

Пусни го СЛЕД run_all.py, преди да качиш нов products.json:
    cd scraper
    python3 run_all.py
    python3 cleanup_placeholder_data.py
    python3 validate_data.py

Продукт, останал без нито една реална оферта след почистването, се
маркира явно (не се трие автоматично) — прегледай изхода и реши дали
да го премахнеш ръчно, или да изчакаш скрапер, който да го покрие.
"""

import json

DATA_PATH = "../data/products.json"


def is_fake_offer(offer: dict) -> bool:
    img = offer.get("image") or ""
    url = offer.get("url") or ""
    return "placehold.co" in img or "produkt-demo" in url


def main(remove_empty: bool = False):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    removed = 0
    now_empty = []

    for p in data["products"]:
        fake_store_ids = [sid for sid, offer in p["offers"].items() if is_fake_offer(offer)]
        for sid in fake_store_ids:
            del p["offers"][sid]
            removed += 1
        if not p["offers"]:
            now_empty.append(p["id"])

    if remove_empty and now_empty:
        data["products"] = [p for p in data["products"] if p["offers"]]

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Премахнати фалшиви оферти: {removed}")
    if now_empty:
        action = "премахнати от файла" if remove_empty else "останаха в файла, но НЕ се показват на сайта"
        print(f"\n⚠ {len(now_empty)} продукта {action} (нямат нито една реална оферта):")
        for pid in now_empty:
            print(f"  - {pid}")
    print("\nГотово. Пусни validate_data.py, за да провериш резултата.")


if __name__ == "__main__":
    import sys
    main(remove_empty="--remove-empty" in sys.argv)
