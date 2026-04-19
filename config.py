"""
config.py — Paramètres de connexion aux bases de données.
Charge les variables d'environnement depuis .env si présent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB",  "mamionmiam")

# Neo4J
NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mamionmiam")

# Dossier des fichiers JSON bruts
DATA_DIR    = os.getenv("DATA_DIR", "data")
EXPORTS_DIR = os.getenv("EXPORTS_DIR", "exports")
