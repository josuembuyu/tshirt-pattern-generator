# Déploiement

## Construire le frontend

```bash
npm install --prefix frontend
npm --prefix frontend run build
```

Les fichiers de production sont générés dans `frontend/dist`. FastAPI sert automatiquement ce dossier lorsqu'il existe.

## Lancer l'API

```bash
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Reverse proxy

Pointer le proxy vers `127.0.0.1:8000`. L'API utilise `/api/*`; l'application React est servie sur les autres routes après build.

## Notes production

- Placer FastAPI derrière Nginx ou Caddy pour TLS.
- Utiliser systemd, supervisord ou Docker pour gérer le process.
- Garder les fichiers exportés éphémères : l'implémentation actuelle les stream depuis la mémoire.
- Ajouter une authentification avant d'exposer le stockage de projets ou des espaces de travail persistants.

## Railway — pas à pas (recommandé)

Un seul service : le `Dockerfile` à la racine build le frontend puis lance FastAPI (UI + `/api` sur le même domaine).

### Avant

1. **Code sur GitHub** (ou GitLab que Railway supporte) : crée un dépôt, puis dans le dossier du projet :
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TON_USER/TON_REPO.git
   git push -u origin main
   ```
2. Vérifie en local que le déploiement Docker a du sens (optionnel mais utile) :
   ```bash
   docker build -t ateliercad .
   docker run --rm -p 8000:8000 -e PORT=8000 ateliercad
   ```
   Ouvre `http://localhost:8000` et `http://localhost:8000/api/health` (tu dois voir du JSON `status: ok`).

### Sur Railway

1. Va sur [railway.app](https://railway.app) → crée un compte (souvent **Login with GitHub**).
2. **New project** → **Deploy from GitHub repo** (ou équivalent).
3. Autorise Railway à lire tes dépôts si demandé → **choisis le repo** `tshirt_pattern_generator` (ou le nom que tu lui as donné).
4. Railway détecte en général le **`Dockerfile`** à la racine : laisse **Docker** comme builder (pas besoin de Nixpacks séparés).
5. Attends la fin du **Build** puis du **Deploy** (logs dans l’onglet du service). En cas d’erreur mémoire sur `pip install`, augmente la taille du service dans les paramètres du plan / instance.

### URL publique

1. Ouvre le **service** déployé → onglet **Settings** (ou **Networking** selon l’UI).
2. Section **Public networking** → **Generate domain** (ou **Custom domain** si tu as un nom de domaine).
3. Copie l’URL (`https://….up.railway.app` ou similaire).

### Vérifier

- Page d’accueil : l’app React doit s’afficher.
- API : `https://TON_URL/api/health` doit renvoyer JSON avec `"status": "ok"`.

### Variables d’environnement

- **Aucune obligatoire** pour démarrer : Railway injecte **`PORT`** ; le `Dockerfile` l’utilise déjà.
- Tu n’as **`VITE_API_URL`** que si tu sers le front sur un autre domaine que l’API (ce n’est pas le cas ici).

### Mettre à jour après un `git push`

- Railway redéploie en général **automatiquement** sur chaque push vers la branche connectée (souvent `main`). Sinon : **Deployments → Redeploy**.

## Test local de l’image Docker

```bash
docker build -t ateliercad .
docker run --rm -p 8000:8000 -e PORT=8000 ateliercad
```

Puis `http://localhost:8000` et `http://localhost:8000/api/health`.
