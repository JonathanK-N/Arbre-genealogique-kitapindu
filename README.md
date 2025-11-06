# Arbre généalogique Kitapindu

Plateforme professionnelle pour gérer, visualiser et valoriser l’héritage de la famille Kitapindu. Le projet s’appuie sur Flask, une base SQLite pilotée par SQLAlchemy, et une visualisation interactive propulsée par D3.js.

## Démarrage rapide

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
flask --app app run --port 8080
```

L’application crée automatiquement la base `instance/kitapindu.db` avec un jeu de données représentatif (six générations, lignes féminines et masculines).

## Accès

- Site public : http://localhost:8080  
- Administration : http://localhost:8080/admin  
  - Utilisateur : `admin`
  - Mot de passe : `kitapindu2024`

## Fonctionnalités clés

- Arbre généalogique interactif (modes vertical, horizontal, radial et compact) avec zoom, recherche, recentrage et réglage de profondeur jusqu’à la 6ᵉ génération.
- Représentation par unions familiales : couples et parents isolés sont regroupés pour valoriser les lignées féminines comme masculines.
- Photos de profil grâce à des placeholders dynamiques (ou images personnalisées via le champ `photo`).
- Tableau de bord d’administration pour créer, filtrer et supprimer des fiches membres.
- API REST (`/api/v1`) pour consommer ou intégrer les données dans d’autres outils.
- Charte graphique revisitée (palette bicolore indigo/safranné) et sections dynamiques (badges, statistiques, chroniques à venir).

## Structure du projet

- `app/` : application Flask modulaire (config, modèles, routes, services).
- `static/` : ressources front (CSS, D3.js, scripts d’administration, placeholders).
- `templates/` : pages HTML (public + back-office).
- `instance/kitapindu.db` : base SQLite générée à la volée.
- `requirements.txt` : dépendances Python.

## API

| Verbe  | Route                  | Description                               |
|--------|------------------------|-------------------------------------------|
| GET    | `/api/v1/members`      | Liste des membres, filtre par `?search=` |
| GET    | `/api/v1/members/<id>` | Détails d’un membre                       |
| POST   | `/api/v1/members`      | Création (authentification requise)      |
| PUT    | `/api/v1/members/<id>` | Mise à jour (authentification requise)   |
| DELETE | `/api/v1/members/<id>` | Suppression (authentification requise)   |
| GET    | `/api/v1/tree`         | Structure hiérarchique prête pour D3     |

## Personnalisation

- Ajuster les données initiales : `app/seed.py`.
- Modifier la présentation de l’arbre ou la charte graphique : `static/js/tree.js`, `static/css/style.css`.
- Étendre l’API ou la logique métier : `app/routes/api.py`, `app/services/family_tree.py`.

## Notes

- Pour repartir de zéro, supprimez `instance/kitapindu.db` avant de relancer l’application.
- Activez `FLASK_ENV=production` et changez `KITAPINDU_SECRET_KEY` avant un déploiement public.
