# Arbre Généalogique Kitapindu

Système de recensement familial avec arbre généalogique interactif.

## Installation

```bash
pip install -r requirements.txt
python app.py
```

## Accès

- **Site public**: http://localhost:8080
- **Administration**: http://localhost:8080/admin
  - Utilisateur: `admin`
  - Mot de passe: `kitapindu2024`

## Fonctionnalités

- Arbre généalogique interactif avec animations D3.js
- Interface d'administration pour gérer les membres
- Base de données SQLite intégrée
- Design responsive avec Bootstrap
- Authentification sécurisée pour l'administration

## Structure

- `app.py` - Application Flask principale
- `templates/` - Templates HTML
- `static/` - CSS, JavaScript et ressources
- `kitapindu.db` - Base de données SQLite (créée automatiquement)