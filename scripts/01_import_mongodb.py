
import json
import os
import sys

from pymongo import MongoClient, GEOSPHERE

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import MONGO_URI, MONGO_DB, DATA_DIR


def load_json(filename: str):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def import_collection(db, name: str, docs: list):
    col = db[name]
    col.drop()
    col.insert_many(docs)
    print(f"  ✓ {name:20s} → {len(docs):>5} documents")
    return col


def prepare_shops(raw: list) -> list:
    """Ajoute un champ GeoJSON Point pour les requêtes géospatiales."""
    for s in raw:
        s["location"] = {
            "type": "Point",
            "coordinates": [float(s["lng"]), float(s["lat"])]
        }
    return raw


def prepare_clients(raw: list) -> list:
    """Ajoute un champ GeoJSON à partir de coords.lat / coords.lng."""
    for c in raw:
        coords = c.get("coords")
        if coords and "lat" in coords and "lng" in coords:
            c["location"] = {
                "type": "Point",
                "coordinates": [float(coords["lng"]), float(coords["lat"])]
            }
    return raw


def main():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]

    print(f"\n Import MongoDB — base : {MONGO_DB}\n")

    col = import_collection(db, "shops", prepare_shops(load_json("shops.json")))
    col.create_index([("location", GEOSPHERE)])

    col = import_collection(db, "clients", prepare_clients(load_json("clients.json")))
    col.create_index("id", unique=True)
    col.create_index([("location", GEOSPHERE)])

    col = import_collection(db, "parrainages", load_json("parrainages.json"))
    col.create_index("idParrain")
    col.create_index("idFilleul")

    col = import_collection(db, "entreprises", load_json("entreprises.json"))
    col.create_index("siret", unique=True)

    col = import_collection(db, "achats", load_json("achats.json"))
    col.create_index("acheteur")
    col.create_index("ticket", unique=True)

    col = import_collection(db, "produits", load_json("produits.json"))
    col.create_index("SKU", unique=True)

    print("\n Import terminé.\n")
    client.close()


if __name__ == "__main__":
    main()
