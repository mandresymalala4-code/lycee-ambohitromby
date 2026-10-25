# Héberger gratuitement l'application avec un compte Git (GitHub)

**Architecture 100 % gratuite**

| Élément | Service gratuit | Rôle |
|---|---|---|
| Code source | **GitHub** | Dépôt Git, source de tous les déploiements |
| Frontend (React) | **Cloudflare Pages** | Sert le site, se met à jour à chaque `git push` |
| Backend (Django) + base | **PythonAnywhere** (offre *Beginner*) | API, PDF, photos, base **SQLite** |

Résultat : `https://VOTRE-SITE.pages.dev` (l'application) qui appelle `https://VOTRE_NOM.pythonanywhere.com` (l'API).

## À savoir avant de commencer (limites vérifiées en octobre 2026)
- PythonAnywhere gratuit : **1 application web, 512 Mo, 100 secondes de calcul par jour**. Au-delà, le site ralentit jusqu'au lendemain.
- L'application web gratuite **expire au bout d'un mois** : il faut cliquer sur le bouton de prolongation (onglet *Web*) une fois par mois, sinon elle est désactivée.
- **MySQL n'est plus inclus** dans les nouveaux comptes gratuits (depuis janvier 2026) : l'application utilise donc **SQLite** (déjà prévu dans le projet, testé).
- Adresse en `pythonanywhere.com` et `pages.dev` (domaine personnalisé payant côté PythonAnywhere).
- Adapté à une démonstration, un test ou un petit établissement. Pour un usage intensif, l'offre payante de PythonAnywhere (environ 10 $/mois) lève ces limites.
- Les offres gratuites changent : si un écran diffère légèrement de ce guide, suivez le même principe.

---
## ÉTAPE 1 – Créer les comptes (5 min)
1. **GitHub** : https://github.com/signup (gratuit).
2. **PythonAnywhere** : https://www.pythonanywhere.com/ → *Start for free* → compte **Beginner**. Le *nom d'utilisateur* choisi devient l'adresse de l'API : choisissez-le court, en minuscules (`ecoleambo` → `ecoleambo.pythonanywhere.com`).
3. **Cloudflare** : https://dash.cloudflare.com/sign-up (gratuit, aucune carte bancaire nécessaire pour Pages).

## ÉTAPE 2 – Installer Git sur Windows
1. Téléchargez Git : https://git-scm.com/download/win et installez avec les options par défaut.
2. Ouvrez une invite de commandes (cmd) et tapez (une seule fois) :
```
git --version
git config --global user.name "Votre Nom"
git config --global user.email "votre-email-github@exemple.com"
```

## ÉTAPE 3 – Envoyer le projet sur GitHub
1. Sur https://github.com/new : *Repository name* = `lycee-ambohitromby`, **ne cochez rien** (pas de README, pas de .gitignore), **Create repository**. Public ou Private au choix (le fichier `.env` n'est jamais envoyé, voir `.gitignore`).
2. Dans cmd, dans le dossier du projet (là où se trouvent `backend`, `frontend`, `README.md`) :
```
cd C:\lycee-ambohitromby
git init
git add .
git status
```
   **Vérifiez** que la liste ne contient ni `.env`, ni `venv`, ni `node_modules` (ils sont ignorés automatiquement).
```
git commit -m "Version initiale"
git branch -M main
git remote add origin https://github.com/VOTRE_COMPTE_GITHUB/lycee-ambohitromby.git
git push -u origin main
```
   Une fenêtre du navigateur demande de vous connecter à GitHub : acceptez.
3. Actualisez la page GitHub : vous voyez `backend`, `frontend`, `README.md`… (et **pas** de fichier `.env`).

## ÉTAPE 4 – Mettre le backend sur PythonAnywhere
Remplacez partout `VOTRE_NOM` par votre nom d'utilisateur PythonAnywhere et `VOTRE_COMPTE_GITHUB` par votre compte GitHub.

### 4.1 Récupérer le code
PythonAnywhere → onglet **Consoles** → **Bash**, puis :
```
cd ~
git clone https://github.com/VOTRE_COMPTE_GITHUB/lycee-ambohitromby.git lycee
```
(Dépôt privé : `git clone https://VOTRE_COMPTE_GITHUB:VOTRE_JETON@github.com/VOTRE_COMPTE_GITHUB/lycee-ambohitromby.git lycee`, avec un jeton créé sur GitHub → Settings → Developer settings → Personal access tokens, droit *Contents : Read*.)

### 4.2 Environnement Python et dépendances
```
mkvirtualenv --python=python3.12 lycee-env
cd ~/lycee/backend
pip install -r requirements-pythonanywhere.txt
```
Si `python3.12` n'existe pas, essayez `python3.13` ou `python3.11`.

### 4.3 Fichier de configuration `.env`
```
cp .env.production.example .env
python -c "import secrets;print(secrets.token_urlsafe(50))"
nano .env
```
Dans `nano`, modifiez les lignes : `SECRET_KEY=` (collez la clé affichée), `ALLOWED_HOSTS=VOTRE_NOM.pythonanywhere.com`, et laissez provisoirement `CORS_ORIGIN` (vous le corrigerez à l'étape 6). Enregistrez : **Ctrl+O**, **Entrée**, puis **Ctrl+X**.
(Vous pouvez aussi éditer `lycee/backend/.env` depuis l'onglet **Files**.)

### 4.4 Créer la base et le compte administrateur
```
python manage.py migrate
python manage.py creer_admin --email admin@votre-ecole.mg --password UnMotDePasseSolide2026
python manage.py initialiser_etablissement
```
N'exécutez **pas** `charger_demo` en production réelle (comptes de démonstration connus de tous).

### 4.5 Créer l'application web
1. Onglet **Web** → **Add a new web app** → *Next* → **Manual configuration** → **Python 3.12** → *Next*.
2. Section **Code** :
   - *Source code* : `/home/VOTRE_NOM/lycee/backend`
   - *Working directory* : `/home/VOTRE_NOM/lycee/backend`
   - *Virtualenv* : `/home/VOTRE_NOM/.virtualenvs/lycee-env`
3. Cliquez sur le lien **WSGI configuration file** : supprimez tout le contenu et collez :
```python
import os
import sys

chemin = '/home/VOTRE_NOM/lycee/backend'
if chemin not in sys.path:
    sys.path.insert(0, chemin)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```
   Enregistrez (**Save**).
4. Section **Security** : activez **Force HTTPS**.
5. Cliquez sur le gros bouton vert **Reload VOTRE_NOM.pythonanywhere.com**.
6. Test : ouvrez `https://VOTRE_NOM.pythonanywhere.com/api/disciplines/` → vous devez voir `[]`. Aucune configuration de fichiers statiques n'est nécessaire (photos et logo sont servis par l'application).

## ÉTAPE 5 – Mettre le frontend sur Cloudflare
Le projet contient déjà `frontend/wrangler.jsonc` (configuration Cloudflare) et `frontend/.env.production` (adresse de l'API). **Ouvrez `frontend/.env.production` et remplacez `tsiresy` par votre nom d'utilisateur PythonAnywhere** (une seule ligne : `VITE_API_URL=https://VOTRE_NOM.pythonanywhere.com`, sans `/` final), puis `git add .`, `git commit`, `git push`.

1. https://dash.cloudflare.com → **Compute (Workers & Pages)** → **Create** → **Import a repository** (ou *Connect to Git*) → GitHub → dépôt `lycee-ambohitromby`.
2. Réglages :
   - *Project name* : `lycee-ambohitromby` (**identique** au champ `name` de `wrangler.jsonc`)
   - *Build command* : `npm run build`
   - *Deploy command* : `npx wrangler deploy`
   - *Root directory* (Advanced) : `frontend`
   - *Variables de **build*** : `NODE_VERSION` = `20` (et, si vous ne gardez pas `.env.production`, `VITE_API_URL` = `https://VOTRE_NOM.pythonanywhere.com`)
3. **Save and Deploy**. L'adresse obtenue ressemble à `https://lycee-ambohitromby.VOTRE-COMPTE.workers.dev` (sans accent, sans point final).
4. Contrôle : sur le site, **Ctrl+U** doit montrer `src="/assets/index-….js"` (et non `/src/main.jsx`).

*Cloudflare Pages (ancienne interface) fonctionne aussi : Build output `dist`, Root directory `frontend`.*

## ÉTAPE 6 – Relier les deux (autoriser le frontend côté API)
Console Bash PythonAnywhere :
```
nano ~/lycee/backend/.env
```
Mettez `CORS_ORIGIN=https://lycee-ambohitromby.VOTRE-COMPTE.workers.dev` (adresse exacte, celle de l'étape 5 ; pour Cloudflare Pages : `https://XXXX.pages.dev`, sans `/` final ; plusieurs adresses séparées par des virgules). Enregistrez, puis onglet **Web** → **Reload**.

## ÉTAPE 7 – Tester
Ouvrez `https://XXXX.pages.dev`, connectez-vous avec l'administrateur créé à l'étape 4.4. Testez : une classe, une inscription, un PDF, le bouton **À propos**.

---
## Mises à jour (après chaque modification du code)
1. Sur votre PC : 
```
cd C:\lycee-ambohitromby
git add .
git commit -m "Description de la modification"
git push
```
2. **Frontend** : Cloudflare reconstruit tout seul (1 à 2 minutes).
3. **Backend** : console Bash PythonAnywhere :
```
bash ~/lycee/scripts/maj-pythonanywhere.sh
```

## Tâches mensuelles et sauvegardes
- **Chaque mois** : PythonAnywhere → onglet **Web** → bouton de prolongation (*Run until 1 month from today*). Sans cela, l'application web est désactivée.
- **Sauvegarde** (conseillée chaque semaine) : console Bash → `bash ~/lycee/scripts/sauvegarde-pythonanywhere.sh`, puis téléchargez les fichiers du dossier `sauvegardes` depuis l'onglet **Files**. La base est le fichier `~/lycee/backend/db.sqlite3`.

## Sécurité à respecter
- Ne publiez **jamais** `.env` (déjà ignoré par Git). Si une clé ou un mot de passe a fuité, changez-les.
- Utilisez un mot de passe administrateur solide ; ne chargez pas la démo en production.
- `DEBUG=False` en production (déjà dans `.env.production.example`).
- Gardez Force HTTPS activé.

## Dépannage
| Symptôme | Cause / solution |
|---|---|
| Erreur CORS dans le navigateur, « Impossible de contacter le serveur » | `CORS_ORIGIN` ne correspond pas exactement à l'adresse `pages.dev` ; corrigez `.env` puis **Reload**. |
| `Invalid HTTP_HOST header` / `DisallowedHost` | `ALLOWED_HOSTS` doit être `VOTRE_NOM.pythonanywhere.com`. |
| « Something went wrong :-( » / *Unhandled Exception* | Lancez `bash ~/lycee/scripts/diagnostic-pythonanywhere.sh` : il indique la cause (`.env` manquant, virtualenv, paquets, WSGI) et affiche le journal d'erreurs. Voir aussi la section ci-dessous. |
| `ImproperlyConfigured … SECRET_KEY` | Remplacez la valeur `SECRET_KEY` dans `.env` par la clé générée. |
| 404 en actualisant une page (`/classes`) | Cloudflare Pages gère cela tout seul ; vérifiez que *Build output directory* = `dist` et *Root directory* = `frontend`. |
| Le site appelle `localhost` / `127.0.0.1` | `VITE_API_URL` absent à la construction : vérifiez `frontend/.env.production` (ou la variable de build Cloudflare), poussez, puis **Retry build**. |
| Message « Impossible de contacter le serveur (https://…) » | L'adresse entre parenthèses est celle que le site utilise : si elle est fausse → corrigez `.env.production` ; si elle est bonne → `CORS_ORIGIN` ne correspond pas exactement à l'adresse du site (puis **Reload**). |
| Page blanche, `src="/src/main.jsx"` dans Ctrl+U | Le site n'a pas été construit : *Build command* = `npm run build` et *Root directory* = `frontend`. |
| `git push` refusé | Faites d'abord `git pull` (des fichiers ont pu être créés sur GitHub). |
| `pip` échoue | Vérifiez que le virtualenv est actif : `workon lycee-env`. |
| Site lent ou « CPU limit » | Les 100 s/jour de la formule gratuite sont épuisées ; réessayez demain ou passez à l'offre payante. |
| Application indisponible après un mois | Prolongation oubliée : onglet **Web**, bouton de prolongation, puis **Reload**. |
| Photos absentes après un nouveau déploiement | Les photos sont dans `backend/media` (non versionné) ; elles restent sur PythonAnywhere. Ne supprimez pas ce dossier. |

## « Something went wrong :-( » : les causes, dans l'ordre
Ouvrez l'onglet **Web** → lien **Error log** : la **dernière ligne** donne la cause.

| Dernière ligne du journal | Correction |
|---|---|
| `Fichier de configuration introuvable` ou `Error loading MySQLdb module` | `.env` manquant : `cd ~/lycee/backend`, `cp .env.production.example .env`, `nano .env` (voir étape 4.3). |
| `mysqlclient n'est pas installé` | Dans `.env`, mettez `DB_ENGINE=sqlite`. |
| `définissez une SECRET_KEY` | Remplacez `SECRET_KEY` par une clé générée (`python -c "import secrets;print(secrets.token_urlsafe(50))"`). |
| `ModuleNotFoundError: No module named 'django'` (ou `dotenv`, `rest_framework`…) | Le *Virtualenv* de l'onglet Web est vide ou faux : `/home/VOTRE_NOM/.virtualenvs/lycee-env`. Puis `workon lycee-env` et `pip install -r requirements-pythonanywhere.txt`. |
| `ModuleNotFoundError: No module named 'config'` | Chemin faux dans le fichier WSGI : il doit être `/home/VOTRE_NOM/lycee/backend`. |
| `SyntaxError` / `IndentationError` dans le fichier WSGI | Recollez exactement le contenu du guide (indentation de 4 espaces, aucun reste de l'ancien contenu). |
| `no such table` | Lancez `python manage.py migrate` (virtualenv actif). |
| Aucune erreur, mais ancienne page | Cliquez sur **Reload** (bouton vert) puis actualisez avec Ctrl+F5. |

## Alternatives
- **Mode nuit** : bouton lune/soleil en haut ; le choix est mémorisé, même sur l'écran de connexion.
- **Netlify** pour le frontend : `netlify.toml` est déjà fourni (ajoutez la variable `VITE_API_URL` dans *Site settings → Environment variables*). Son offre gratuite est limitée par un système de crédits.
- **Vercel** : l'offre gratuite *Hobby* est réservée à un usage non commercial.
- **MySQL gratuit** : possible uniquement sur d'autres hébergeurs (ou comptes PythonAnywhere créés avant janvier 2026) ; configurez alors `DB_ENGINE=mysql` et les variables `DB_*` du fichier `.env`.
