# Mamion Miam — Projet Data

Analyse des données de la chaîne de magasins **Mamion Miam** (Hauts-de-Seine).  
Stack : **MongoDB** (source de vérité) + **Neo4J** (graphes) + **Python** (scripts d'analyse) + **Jupyter** (notebook interactif).

---

## Structure du projet

```
mamionmiam/
├── docker-compose.yml              # MongoDB + Neo4J
├── config.py                       # Paramètres de connexion (lit .env)
├── requirements.txt
├── analyse.ipynb                   # ← Notebook principal (toutes les analyses)
├── data/                           # Fichiers JSON bruts (ignorés par git)
│   ├── shops.json
│   ├── clients.json
│   ├── parrainages.json
│   ├── entreprises.json
│   ├── achats.json
│   └── produits.json
├── scripts/
│   ├── 01_import_mongodb.py        # Charge les JSON dans MongoDB
│   ├── 03_import_neo4j_parrainage.py  # Alimente Neo4J (graphe parrainage)
│   └── 05_import_neo4j_ventes.py   # Alimente Neo4J (graphe ventes)
└── exports/                        # PNGs des graphiques générés
```

---

## Mise en place

### 1. Prérequis

- [Python 3.12+](https://www.python.org/downloads/) — cocher "Add to PATH" à l'installation
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 2. Cloner et préparer

```bash
git clone <url-du-repo>
cd mamionmiam
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Télécharger les données

```bash
cd data
curl -O https://data.atontour.info/IABD/mamionmiam.zip
unzip mamionmiam.zip
mv mamionmiam/*.json .
cd ..
```

### 4. Lancer les bases de données

```bash
docker-compose up -d
```

- MongoDB : `localhost:27017`
- Neo4J Browser : http://localhost:7474 (login : `neo4j` / `mamionmiam`)

### 5. Variables d'environnement (optionnel)

Créer un fichier `.env` pour surcharger les valeurs par défaut :

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=mamionmiam
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mamionmiam
DATA_DIR=data
EXPORTS_DIR=exports
```

---

## Workflow d'exécution

### Étape 1 — Charger les données (à faire une seule fois)

```bash
python scripts/01_import_mongodb.py
python scripts/03_import_neo4j_parrainage.py
```

### Étape 2 — Lancer le notebook

```bash
venv\Scripts\jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=mamionmiam analyse.ipynb
```

Les graphiques PNG sont générés automatiquement dans `exports/` à chaque exécution.

> Ou ouvrir `analyse.ipynb` dans VS Code / Jupyter et sélectionner le kernel **Python (mamionmiam)**.

### Étape 3 (optionnel) — Graphe des ventes dans Neo4J

```bash
python scripts/05_import_neo4j_ventes.py
```

> ⚠️ Ce script **réinitialise Neo4J**. Ne pas lancer si le graphe parrainage est actif.

---

## Analyses couvertes

### Analyse des ventes (`analyse.ipynb` — section ventes)

| # | Question | Graphique |
|---|----------|-----------|
| Q1 | Top 10 catégories par nombre de produits | ✅ PNG |
| Q2 | Top 10 rayons par nombre de catégories | — |
| Q3 | Top 10 rayons par nombre de produits | ✅ PNG |
| Q4 | Produits souvent achetés ensemble | — |
| Q5 | Catégories avec le plus de lignes de vente | — |
| Q6 | Catégories avec le plus de quantité vendue | — |
| Q7 | Achats et dépense par genre H/F | ✅ PNG |
| Q8 | Achats et dépense par genre et par rayon | ✅ PNG |
| Q9 | Achats et dépense par commune | ✅ PNG |
| Q10 | Dépense par commune et par genre | ✅ PNG |

### Analyse du parrainage (`analyse.ipynb` — section parrainage)

| # | Question | Graphique |
|---|----------|-----------|
| Q1 | Top parrain et ses filleuls | — |
| Q2 | H/F ayant parrainé / été parrainé | — |
| Q3 | Répartition H/F des parrains | ✅ PNG |
| Q4 | Répartition H/F des filleuls | ✅ PNG |
| Q5 | Parrains par tranche d'âge | ✅ PNG |
| Q6 | Chaîne de parrainage la plus longue | — |
| Q7 | Entreprise avec le plus d'employés fidèles | — |
| Q8 | Domaines d'activité les plus représentés | ✅ PNG |
| Q9 | Top 10 entreprises — parrains générés | ✅ PNG |
| Q10 | Abonnés fidélité dans un rayon de 4 km | ✅ PNG |