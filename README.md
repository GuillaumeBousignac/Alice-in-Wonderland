# Bookworm — Moteur NLP
Un outil en ligne de commande CLI qui génère des fiches de livres à partir de différents livres.
À partir d'un identifiant de livre, il calcule des métriques de diversité lexicale, identifie les thèmes, les personnages nommés, les lieux nommés. Il peut produire un résumé structuré et trouver des livres similaires parmi un catalogue de plus de 60 000 titres.

---

## Structure du projet

```
bookworm/
├── bookworm.py           # Point d'entrée CLI
├── data_loader.py        # Téléchargement des livres
├── tools.py              # Outils
├── clean_data.py         # Script de nettoyage du catalogue
├── cleaned_catalog.csv   # Catalogue livres en CSV
├── requirements.txt      # Librairies Python
├── setup.py              # Script d'installation complet
│
├── nlp/
│   ├── lexdiv.py         # Métriques de diversité lexicale
│   ├── card.py           # Résumé de tout les calculs en une carte structurée
│   ├── find.py           # Outils de recherche de livres
│   ├── topics.py         # Modélisation des thèmes
│   ├── entities.py       # Reconnaissance d'entités nommées
│   ├── summarize.py      # Résumé structuré
│   └── similar.py        # Similarité entre livres
│
├── books/                # Livres téléchargés (créé automatiquement)
└── cache/                # Résultats des commandes (créé automatiquement)
```

---

## Installation

**1. Cloner le dépôt**

```bash
git clone <url-du-repo>
cd bookworm
```

**2. Créer et activer un environnement virtuel**

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

**3. Lancer le script d'installation**

```bash
python setup.py
```

Ce script installe automatiquement toutes les librairies python indispensables pour le fonctionnemement du projet en une seule commande.

---

## Utilisation

Toutes les commandes (sauf --find) suivent le même schéma :

```bash
python bookworm.py --<commande> <ID>
```

L'`<ID>` correspond à l'identifiant d'un livre.
Si le livre n'a pas encore été téléchargé, il est téléchargé automatiquement.

```bash
python bookworm.py --find --title / --author / --category <"Texte">
```

Le `<"Texte">` correspond à un titre, un nom ou à une catégorie que vous souhaitez rechercher.

### Commandes disponibles

| Commande | Description |
|---|---|
| `--lexdiv <ID>` | Métriques de diversité lexicale |
| `--topics <ID>` | Modélisation des thèmes |
| `--entities <ID>` | Personnages et lieux dans le livres|
| `--summarize <ID>` | Résumé structuré |
| `--similar <ID>` | 5 livres les plus similaires |
| `--card <ID>` | Fiche complète — toutes les métriques combinées |
| `--find --title / --author / --category <"Texte">` | Outils de recherche à partir de texte |

### Exemples

```bash
# Diversité lexicale d'Alice au pays des merveilles
python bookworm.py --lexdiv 11

# Modélisation des thèmes de Frankenstein
python bookworm.py --topics 84

# Personnages et lieux dans Orgueil et Préjugés
python bookworm.py --entities 1342

# Résumé de Dracula
python bookworm.py --summarize 345

# Livres similaires à La Guerre des mondes
python bookworm.py --similar 36

# Fiche complète d'Alice au pays des merveilles
python bookworm.py --card 11

# Cherche tous les livres ayant pour titre "alice adventure in wonderland"
python bookworm.py --find --title "alice adventure in wonderland"

# Cherche tous les livres ayant pour auteur "LoveCraft"
python bookworm.py --find --author "LoveCraft"

# Cherche tous les livres ayant la catégorie "fantasy"
python bookworm.py --find --category "fantasy"
```

---

## Cache

Les résultats sont automatiquement mis en cache dans le dossier `cache/` pour garder un historique de chaque commande.

| Fichier | Contenu |
|---|---|
| `cache/<id>_lexdiv.json` | Diversité lexicale |
| `cache/<id>_topics.json` | Résultats de modélisation des thèmes |
| `cache/<id>_entities.json` | Entités nommées et lieux |
| `cache/<id>_summarize.json` | Résumé |
| `cache/<id>_similar.json` | Liste des livres similaires |
| `cache/catalog_tfidf.pkl` | Matrice TF-IDF pour la similarité |

Pour recalculer un résultat, il suffit de supprimer le fichier de cache correspondant :

```bash
rm cache/11_summarize.json
python bookworm.py --summarize 11
```