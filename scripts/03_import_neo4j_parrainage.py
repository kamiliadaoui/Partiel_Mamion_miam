"""
03_import_neo4j_parrainage.py
==============================
Alimente Neo4J pour l'analyse du parrainage.
Source de vérité : MongoDB.

Schéma Neo4J créé :
  (Shop)-[:SPONSOR]->(Usr)           ← non implémenté ici, cf Q10 en MongoDB
  (Usr)-[:SPONSORED {date}]->(Usr)
  (Usr)-[:WORKS_AT]->(Ent)
  (Ent)-[:IN_DOMAIN]->(Domain)
  (Ent)-[:IN_NAF]->(NAF)

Structure réelle :
  clients.json     : entreprise = {siret, nom}  (pas de coords dans entreprise)
  entreprises.json : siret, nom, domain_code/label, naf_code/label
  parrainages.json : idParrain, idFilleul, dateParrainage

  Ce script VIDE Neo4J avant import.
État requis  : MongoDB alimenté (01_import_mongodb.py)
Usage        : python scripts/03_import_neo4j_parrainage.py
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


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------
print("\n  Vidage de Neo4J…")
with driver.session() as s:
    s.run("MATCH (n) DETACH DELETE n")
print("   OK")


# ---------------------------------------------------------------------------
# Contraintes
# ---------------------------------------------------------------------------
print(" Contraintes…")
with driver.session() as s:
    for cql in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:Usr)    REQUIRE u.id    IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Ent)    REQUIRE e.siret IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.code  IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:NAF)    REQUIRE n.code  IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Shop)   REQUIRE s.id    IS UNIQUE",
    ]:
        s.run(cql)


# ---------------------------------------------------------------------------
# Nœuds Usr  (781 clients)
# ---------------------------------------------------------------------------
print(" Clients (Usr)…")
clients = list(db.clients.find({}, {"_id": 0}))

BATCH = 200
with driver.session() as s:
    for i in range(0, len(clients), BATCH):
        batch = clients[i:i + BATCH]
        s.run("""
            UNWIND $batch AS c
            MERGE (u:Usr {id: c.id})
            SET u.nom        = c.nom,
                u.prenom     = c.prenom,
                u.genre      = c.genre,
                u.naissance  = c.naissance,
                u.commune    = c.commune,
                u.code_postal = c.code_postal,
                u.lat        = c.coords.lat,
                u.lng        = c.coords.lng
        """, batch=batch)
print(f"   {len(clients)} nœuds")


# ---------------------------------------------------------------------------
# Nœuds Shop (4 boutiques)
# ---------------------------------------------------------------------------
print(" Boutiques (Shop)…")
shops = list(db.shops.find({}, {"_id": 0}))
with driver.session() as s:
    s.run("""
        UNWIND $shops AS sh
        MERGE (shop:Shop {id: sh.id})
        SET shop.name    = sh.name,
            shop.adresse = sh.adresse,
            shop.lat     = sh.lat,
            shop.lng     = sh.lng
    """, shops=shops)
print(f"   {len(shops)} nœuds")


# ---------------------------------------------------------------------------
# Nœuds Ent + Domain + NAF  (54 entreprises)
# ---------------------------------------------------------------------------
print(" Entreprises (Ent + Domain + NAF)…")
entreprises = list(db.entreprises.find({}, {"_id": 0}))
with driver.session() as s:
    for e in entreprises:
        s.run("""
            MERGE (ent:Ent {siret: $siret})
            SET ent.nom   = $nom,
                ent.ville = $ville

            MERGE (d:Domain {code: $domain_code})
            SET d.label = $domain_label

            MERGE (n:NAF {code: $naf_code})
            SET n.label = $naf_label

            MERGE (ent)-[:IN_DOMAIN]->(d)
            MERGE (ent)-[:IN_NAF]->(n)
        """,
        siret=e["siret"], nom=e["nom"], ville=e.get("ville", ""),
        domain_code=e.get("domain_code", "?"),
        domain_label=e.get("domain_label", "?"),
        naf_code=e.get("naf_code", "?"),
        naf_label=e.get("naf_label", "?"),
        )
print(f"   {len(entreprises)} nœuds Ent")


# ---------------------------------------------------------------------------
# Relation Usr -[:WORKS_AT]-> Ent
# Clients avec entreprise = {siret, nom}
# ---------------------------------------------------------------------------
print(" Liens WORKS_AT…")
clients_ent = [c for c in clients if c.get("entreprise") and c["entreprise"].get("siret")]
with driver.session() as s:
    for i in range(0, len(clients_ent), BATCH):
        batch = [{"uid": c["id"], "siret": c["entreprise"]["siret"]}
                 for c in clients_ent[i:i + BATCH]]
        s.run("""
            UNWIND $batch AS row
            MATCH (u:Usr {id: row.uid})
            MATCH (e:Ent {siret: row.siret})
            MERGE (u)-[:WORKS_AT]->(e)
        """, batch=batch)
print(f"   {len(clients_ent)} liens")


# ---------------------------------------------------------------------------
# Relations SPONSORED  (546 parrainages)
# ---------------------------------------------------------------------------
print(" Parrainages (SPONSORED)…")
parrainages = list(db.parrainages.find({}, {"_id": 0}))
with driver.session() as s:
    for i in range(0, len(parrainages), BATCH):
        batch = parrainages[i:i + BATCH]
        s.run("""
            UNWIND $batch AS p
            MATCH (parrain:Usr {id: p.idParrain})
            MATCH (filleul:Usr {id: p.idFilleul})
            MERGE (parrain)-[r:SPONSORED]->(filleul)
            SET r.date = p.dateParrainage
        """, batch=batch)
print(f"   {len(parrainages)} relations")


driver.close()
mongo.close()
print("\n Import Neo4J (parrainage) terminé.\n")
