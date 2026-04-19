"""
05_import_neo4j_ventes.py
==========================
Alimente Neo4J pour l'analyse des ventes.
Source de vérité : MongoDB.

Schéma :
  (Usr)-[:HAS_BOUGHT]->(Ticket)-[:CONTAINS {qte, total}]->(Produit)
  (Produit)-[:IN_CAT]->(Categorie)-[:IN_RAYON]->(Rayon)

  Ce script VIDE Neo4J avant import.
    Ne pas lancer si le graphe parrainage est actif.

État requis : MongoDB alimenté (01_import_mongodb.py)
Usage       : python scripts/05_import_neo4j_ventes.py
"""

import os
import sys

from pymongo import MongoClient
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import MONGO_URI, MONGO_DB, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

mongo  = MongoClient(MONGO_URI)
db     = mongo[MONGO_DB]
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print("\n  Reset Neo4J…")
with driver.session() as s:
    s.run("MATCH (n) DETACH DELETE n")

print(" Contraintes…")
with driver.session() as s:
    for cql in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:Usr)       REQUIRE u.id  IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Ticket)    REQUIRE t.id  IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Produit)   REQUIRE p.sku IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Categorie) REQUIRE c.nom IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Rayon)     REQUIRE r.nom IS UNIQUE",
    ]:
        s.run(cql)

# ---------------------------------------------------------------------------
# Produits → Categorie → Rayon  (130 produits, 26 cat, 4 rayons)
# ---------------------------------------------------------------------------
print(" Produits…")
produits = list(db.produits.find({}, {"_id": 0}))
BATCH = 50
with driver.session() as s:
    for i in range(0, len(produits), BATCH):
        batch = produits[i:i + BATCH]
        s.run("""
            UNWIND $batch AS p
            MERGE (prod:Produit   {sku: p.SKU})
            SET prod.label = p.Label,
                prod.prix  = p.Prix,
                prod.marque = p.Marque

            MERGE (cat:Categorie  {nom: p.Categorie})
            MERGE (ray:Rayon      {nom: p.Rayon})
            MERGE (prod)-[:IN_CAT]->(cat)
            MERGE (cat)-[:IN_RAYON]->(ray)
        """, batch=batch)
print(f"   {len(produits)} produits, sous-graphe Categorie/Rayon créé")

# ---------------------------------------------------------------------------
# Achats : Usr → Ticket → Produits  (1422 tickets)
# ---------------------------------------------------------------------------
print(" Achats (tickets + lignes)…")
achats = list(db.achats.find({}, {"_id": 0}))

with driver.session() as s:
    for a in achats:
        # Nœud Ticket + lien Usr
        s.run("""
            MERGE (u:Usr    {id: $acheteur})
            MERGE (t:Ticket {id: $ticket})
            SET t.date = $date, t.total = $total
            MERGE (u)-[:HAS_BOUGHT]->(t)
        """,
        acheteur=a["acheteur"],
        ticket=a["ticket"],
        date=str(a.get("date", "")),
        total=float(a.get("total", 0))
        )
        # Lignes du ticket
        for item in a.get("detail", []):
            s.run("""
                MATCH (t:Ticket {id: $ticket})
                MERGE (p:Produit {sku: $sku})
                MERGE (t)-[r:CONTAINS]->(p)
                SET r.qte = $qte, r.total = $total
            """,
            ticket=a["ticket"],
            sku=item["SKU"],
            qte=int(item.get("qte", 1)),
            total=float(item.get("total", 0))
            )

print(f"   {len(achats)} tickets importés")

driver.close()
mongo.close()
print("\n Import Neo4J (ventes) terminé.\n")
