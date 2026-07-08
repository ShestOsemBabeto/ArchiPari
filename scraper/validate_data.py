"""
validate_data.py
-----------------
Автоматична проверка на data/products.json след всяко пускане на
run_all.py. Засича чести грешки, преди да са стигнали до сайта:
липсващи полета, нереалистични цени, счупени връзки към снимки и др.

Стартиране:
    cd scraper
    python validate_data.py
"""

import json
import sys
import urllib.request

DATA_PATH = "../data/products.json"

REQUIRED_PRODUCT_FIELDS = {"id", "name", "category", "unit", "offers"}
REQUIRED_OFFER_FIELDS = {"price", "image", "url"}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_image_reachable(url, timeout=5):
    """Бърза HEAD проверка дали снимка/линк реално отговаря (не 404)."""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except Exception:
        return False


def main(check_links=False):
    errors = []
    warnings = []

    try:
        data = load(DATA_PATH)
    except FileNotFoundError:
        print(f"ГРЕШКА: не намерих {DATA_PATH}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ГРЕШКА: {DATA_PATH} не е валиден JSON: {e}")
        sys.exit(1)

    store_ids = {s["id"] for s in data.get("stores", [])}
    seen_ids = set()

    for i, p in enumerate(data.get("products", [])):
        where = f"products[{i}] (id={p.get('id')})"

        missing = REQUIRED_PRODUCT_FIELDS - p.keys()
        if missing:
            errors.append(f"{where}: липсват полета {missing}")
            continue

        if p["id"] in seen_ids:
            errors.append(f"{where}: дублиран id!")
        seen_ids.add(p["id"])

        if not p["offers"]:
            warnings.append(f"{where}: няма нито една оферта (offers е празно)")

        for store_id, offer in p["offers"].items():
            owhere = f"{where} -> оферта на '{store_id}'"

            if store_id not in store_ids:
                warnings.append(f"{owhere}: store_id не е регистриран в data['stores']")

            missing_offer = REQUIRED_OFFER_FIELDS - offer.keys()
            if missing_offer:
                errors.append(f"{owhere}: липсват полета {missing_offer}")
                continue

            price = offer["price"]
            if not isinstance(price, (int, float)) or price <= 0:
                errors.append(f"{owhere}: невалидна цена ({price!r})")
            elif price > 5000:
                warnings.append(f"{owhere}: подозрително висока цена ({price} лв.) — провери дали не е сгрешена десетична точка")
            elif price < 0.10:
                warnings.append(f"{owhere}: подозрително ниска цена ({price} лв.)")

            if not offer.get("image"):
                warnings.append(f"{owhere}: няма снимка (ще се ползва placeholder)")
            if not offer.get("url"):
                warnings.append(f"{owhere}: няма линк към продукта в магазина")

            if check_links and offer.get("image"):
                ok = check_image_reachable(offer["image"])
                if ok is False:
                    warnings.append(f"{owhere}: снимката не отговаря (възможно счупен линк): {offer['image']}")

    print(f"Продукти: {len(data.get('products', []))}")
    print(f"Магазини: {len(data.get('stores', []))}")
    print()

    if errors:
        print(f"❌ {len(errors)} ГРЕШКИ (трябва да се оправят):")
        for e in errors:
            print(f"  - {e}")
        print()

    if warnings:
        print(f"⚠️  {len(warnings)} предупреждения (не чупят сайта, но си струва да провериш):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if not errors and not warnings:
        print("✅ Всичко изглежда наред.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    check_links = "--check-links" in sys.argv
    if check_links:
        print("(проверявам и дали снимките реално отговарят — може да отнеме време)\n")
    main(check_links=check_links)
