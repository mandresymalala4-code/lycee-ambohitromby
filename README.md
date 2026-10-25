# Gestion d'étude dans un lycée – LYCÉE AMBOHITROMBY

Application web complète (Windows 11 + XAMPP) pour gérer les années scolaires, classes, élèves, inscriptions et reçus, professeurs (avec validation des comptes), matières, emplois du temps, appels et absences, notes, moyennes, classements et bulletins PDF.

Deux interfaces au même design : **Administrateur** (toute la gestion) et **Professeur** (consultation, emploi du temps personnel, appel et notes **uniquement pour sa matière**).

> **Héberger gratuitement avec GitHub** (Cloudflare Pages + PythonAnywhere) : voir **DEPLOIEMENT.md**.

## Technologies
- **Backend** : Python 3.12, Django 5.2 LTS, Django REST Framework, JWT (simplejwt), django-cors-headers, mysqlclient, Pillow, ReportLab
- **Frontend** : React 18 + Vite, React Router, Axios, Recharts, Framer Motion, React Hook Form, lucide-react (CSS maison, thèmes clair/sombre)
- **Base** : MySQL / MariaDB (XAMPP), base `lycee_ambohitromby`, utf8mb4

## Prérequis (à installer une seule fois)
1. **Python 3.12** – https://www.python.org/downloads/ – cochez *Add python.exe to PATH*.
2. **Node.js LTS** – https://nodejs.org/
3. **XAMPP** – https://www.apachefriends.org/ (seul MySQL est nécessaire).

## Installation pas à pas
### 1. Démarrer MySQL
Ouvrez le *XAMPP Control Panel* puis cliquez sur **Start** en face de **MySQL** (port 3306).

### 2. Créer la base
Ouvrez http://localhost/phpmyadmin → **Nouvelle base de données** → nom `lycee_ambohitromby`, interclassement `utf8mb4_unicode_ci` → **Créer**.
(Alternative : onglet *Importer* de phpMyAdmin avec `database/lycee_ambohitromby.sql`, qui crée la base, les tables, les 26 années 2020-2046, leurs trimestres et les 7 classes ; dans ce cas, sautez `migrate`.)

### 3. Configurer
`backend\.env` est déjà prêt pour XAMPP (root, mot de passe vide, 127.0.0.1:3306). Un modèle `.env.example` est fourni. Changez `SECRET_KEY` en production.

### 4. Backend (invite de commandes dans le dossier du projet)
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py creer_admin
python manage.py initialiser_etablissement
python manage.py charger_demo
python manage.py runserver
```
- `creer_admin` demande l'email et le mot de passe (ou : `python manage.py creer_admin --email admin@ambohitromby.mg --password Admin12345`).
- `charger_demo` est facultatif (6 professeurs, 40 élèves, absences, notes sur 2 trimestres). `python manage.py effacer_demo` supprime uniquement ces données.
- Raccourci : double-cliquez sur `demarrer-backend.bat` (crée le venv, installe, migre, démarre).

### 5. Frontend (second invite de commandes)
```
cd frontend
npm install
npm run dev
```
Raccourci : `demarrer-frontend.bat`.

### 6. Ouvrir l'application
- Application : **http://localhost:5173**
- API : **http://127.0.0.1:8000/api/**

## Identifiants de démonstration
| Rôle | Email | Mot de passe |
|---|---|---|
| Administrateur (si créé avec la ligne ci-dessus) | admin@ambohitromby.mg | Admin12345 |
| Professeurs (après `charger_demo`) | prof1@demo.ambohitromby.mg … prof6@demo.ambohitromby.mg | Prof12345 |

prof1 = Mathématiques, prof2 = Français, prof3 = Anglais, prof4 = Physique-Chimie, prof5 = SVT, prof6 = Histoire-Géographie.

## Structure
```
backend/    config/ (réglages) · comptes/ · scolarite/ · notes/ · absences/ · documents/ (PDF + statistiques) · tests/
frontend/   src/ (api.js, context.jsx, ui.jsx, layout.jsx, pages/)
database/   lycee_ambohitromby.sql
documentation/  cahier des charges (.docx)
```

## Fonctionnalités
**Administrateur** : tableau de bord (statistiques animées, graphiques, alertes) · classes et droits · élèves (fiche, modification, suppression, PDF) · inscription en 4 étapes avec reçu PDF et réinscription · professeurs et validation / refus / suspension des comptes · matières et coefficients · emploi du temps (grille cliquable, détection des conflits classe/professeur) · appel et absences, récapitulatifs mensuel/trimestriel, alertes > 15 h, rapports PDF · notes, résultats, classement avec ex æquo, bulletins PDF individuels ou de classe, décision du conseil · paramètres (établissement, logo, année courante, trimestres, clôture) · profil.
**Professeur** : consultation des classes, élèves (sans montants), professeurs, matières · emploi du temps personnel automatique (+ PDF) · appel et notes pour sa seule matière (les autres sont grisées dans l'interface et refusées en **403** par l'API) · profil.
**Sécurité** : JWT (rafraîchissement automatique, déconnexion à l'expiration et après 30 min d'inactivité), mots de passe hashés PBKDF2, verrouillage 15 min après 5 échecs, permissions par rôle et par propriété, CORS limité à `http://localhost:5173`, uploads contrôlés (JPG/PNG, 2 Mo), erreurs JSON `{status, code, message, champs}` (jamais d'erreur 500 brute).

## Choix techniques appliqués (chapitre 15 du cahier des charges)
1. Naissance des élèves : 01/01/1998 – 31/12/2013 (constantes dans `config/settings.py`).
2. Droit d'inscription = total par classe au départ (50 000 / 60 000 / 70 000 Ar), caisse de soutien à 0 ; modifiable dans *Classes*.
3. Matricule automatique `AAAA-NNNN`, immuable ; listes triées alphabétiquement avec N° d'ordre.
4. Paiement intégral à l'inscription (pas de tranches).
5. Modes de paiement : Espèces, MVola, Orange Money, Airtel Money, Chèque/Virement.
6. Une seule matière par professeur.
7. CIN du professeur : exactement 14 chiffres (espaces tolérés à la saisie), unique.
8. Trimestres par défaut : 01/10–31/12, 01/01–31/03, 01/04–30/06 (modifiables dans *Paramètres*).
9. Barème d'appréciation du §8.3 (< 5 Très insuffisant … ≥ 18 Excellent).
10. Alerte : plus de 15 h d'absences **injustifiées** par trimestre et par élève (15 h exactes = pas d'alerte).
11. Matières sans note complète exclues du total des coefficients ; bulletin marqué « Provisoire ».
12. Professeur : au moins 21 ans, né après le 01/01/1950 ; administrateur : au moins 18 ans.
13. Téléphone de l'établissement : 03X ou 02X ; téléphones personnels : 03X (10 chiffres).
14. Informations du concepteur : à fournir par le propriétaire.
15. Le professeur voit la fiche élève en lecture, sans paiement ; contacts des parents visibles.

Calculs : note trimestrielle = (DS + Examen) / 2 ; points = note × coefficient ; moyenne = total points / total coefficients ; rang avec ex æquo (1, 2, 2, 4) recalculé à chaque saisie.
Autres choix : la liste « Élèves » est liée à l'inscription de l'année choisie (ses identifiants sont ceux des inscriptions) ; supprimer une inscription conserve le reçu avec le statut « Annulé » ; un trimestre clôturé reste modifiable par l'administrateur (journalisé).

## Nouveautés de la version 1.2
- **Mode nuit complet** : fond, tableaux, formulaires, graphiques, calendriers natifs, listes déroulantes, fenêtres, emploi du temps et écran de connexion sont entièrement sombres ; le choix est mémorisé (même avant connexion). Le MPD existe en **version nuit** (`mpd-nuit.pdf`), choisie automatiquement.
- **Filtres alignés** (listes déroulantes compactes sur une ligne) dans Élèves, Notes, Absences, etc.
- **Hébergement sans erreur** : `frontend/wrangler.jsonc` et `frontend/.env.production` fournis ; le message « Impossible de contacter le serveur » affiche l'adresse d'API utilisée ; script `scripts/diagnostic-pythonanywhere.sh` ; messages d'erreur de démarrage explicites (`.env` absent, `mysqlclient` manquant).

## Nouveautés de la version 1.1
- **Sécurité de session / retour arrière** : en-têtes `Cache-Control: no-store, no-cache, must-revalidate` sur toute l'API et les PDF (middleware `comptes/middleware.py`) et balises meta dans `index.html` ; après déconnexion, la flèche « Retour » du navigateur ne ramène plus sur une page protégée (historique verrouillé avec `history.pushState`, contrôle au retour depuis le cache du navigateur, déconnexion synchronisée entre onglets) ; la déconnexion **invalide côté serveur** le jeton de rafraîchissement (liste noire) ; jeton expiré ou invalide = retour automatique à la connexion.
- **Design et animations** : police Inter, nouvelle échelle de typographie, ombres et profondeur, navigation à pastille animée, barre de progression entre les pages, apparition progressive des blocs, micro-interactions (boutons, cartes, icônes), fenêtres et toasts adoucis, écran de connexion animé. Les animations respectent `prefers-reduced-motion`.
- **CIN** : exactement **14 chiffres** (formulaires et serveur ; colonne `professeur.cin` en `varchar(14)`, migration `comptes/0002`).
- **Bouton « À propos »** (barre du haut et menu latéral) : fenêtre avec le **MPD (PDF)** intégré, boutons *Agrandir*, *Ouvrir dans un onglet* et *Télécharger*, et onglet « Application ».

### Le PDF du MPD
Le fichier affiché est `frontend/public/documentation/mpd.pdf` (copie dans `documentation/MPD_Lycee_Ambohitromby.pdf`). Il a été **généré automatiquement depuis les modèles** (versions claire `mpd.pdf` et nuit `mpd-nuit.pdf`) (diagramme relationnel + dictionnaire de données de 20 tables).
- **Pour utiliser votre propre PDF** : remplacez simplement `frontend/public/documentation/mpd.pdf` par votre fichier (même nom) ; rien d'autre à modifier.
- **Pour régénérer le MPD** après une modification des modèles : `cd backend`, `venv\Scripts\activate`, `pip install pypdf`, `python tools/generer_mpd.py`.

### Mise à jour d'une installation existante (v1.0 vers v1.1)
1. Remplacez les dossiers `backend` et `frontend` par ceux du nouveau ZIP (conservez votre `backend\.env` et votre dossier `backend\venv`).
2. `cd backend`, `venv\Scripts\activate`, `pip install -r requirements.txt`, `python manage.py migrate` (applique la migration du CIN et la liste noire des jetons).
3. `cd ..\frontend`, `npm install` (nouvelle police), `npm run dev`.
4. Les CIN déjà enregistrés sur 12 chiffres restent en base mais devront être corrigés à 14 chiffres à la prochaine modification de la fiche. Pour les professeurs de démonstration : `python manage.py charger_demo --reset`.

## Tests
`cd backend` puis `python manage.py test tests` (43 tests : connexion, comptes professeurs, unicités, inscription transactionnelle, doublons, notes 0–20, moyennes, classement, absences, alerte 15 h, droits du professeur, PDF, CIN à 14 chiffres, en-têtes anti-cache, déconnexion).

## Dépannage
- **« MariaDB 10.5 or later is required (found 10.4.x) »** (XAMPP) : corrigé dans `backend/config/settings.py` (MariaDB 10.4 accepté). Alternative sans MySQL : mettre `DB_ENGINE=sqlite` dans `backend\.env`.
- **MySQL arrêté / « Can't connect to MySQL server »** : démarrez MySQL dans XAMPP (port 3306).
- **« Unknown database 'lycee_ambohitromby' »** : créez la base (étape 2).
- **Erreur à l'installation de `mysqlclient`** : `python -m pip install --upgrade pip` puis relancez `pip install -r requirements.txt` (Python 3.12, 64 bits). Sinon, installez les *Microsoft C++ Build Tools*.
- **Erreur CORS / « Impossible de contacter le serveur »** : le backend doit tourner sur 127.0.0.1:8000 et le frontend sur http://localhost:5173 (pas 127.0.0.1:5173). Adaptez `CORS_ORIGIN` dans `backend\.env` si besoin.
- **Port occupé** : fermez l'autre programme, ou `python manage.py runserver 8001` (puis `VITE_API_URL` dans `frontend\.env`).
- **« python n'est pas reconnu »** : réinstallez Python en cochant *Add python.exe to PATH*, puis rouvrez l'invite de commandes (ou essayez `py -3.12`).
- **PowerShell bloque `venv\Scripts\activate`** : utilisez l'invite de commandes classique (cmd).
