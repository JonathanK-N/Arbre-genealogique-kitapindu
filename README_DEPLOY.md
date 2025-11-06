# Déploiement sur Railway

## 📋 Étapes de déploiement

### 1. Préparer le projet
```bash
git init
git add .
git commit -m "Initial commit"
```

### 2. Créer un compte Railway
- Aller sur [railway.app](https://railway.app)
- Se connecter avec GitHub

### 3. Déployer
- Cliquer sur "New Project"
- Sélectionner "Deploy from GitHub repo"
- Choisir votre repository
- Railway détectera automatiquement Flask

### 4. Variables d'environnement (optionnel)
Dans Railway Dashboard > Variables :
- `SECRET_KEY` : Clé secrète pour la production
- `PORT` : Géré automatiquement par Railway

## 🔧 Fichiers créés pour le déploiement

- `Procfile` : Commande de démarrage
- `requirements.txt` : Dépendances Python
- `runtime.txt` : Version Python
- `railway.json` : Configuration Railway
- `.gitignore` : Fichiers à exclure

## 🚀 URL d'accès
Après déploiement : `https://votre-app.railway.app`

## 👤 Identifiants admin
- Utilisateur : `admin`
- Mot de passe : `kitapindu2024`

## 📝 Notes importantes
- La base SQLite sera recréée à chaque déploiement
- Les données d'exemple sont automatiquement ajoutées
- L'application fonctionne en mode production