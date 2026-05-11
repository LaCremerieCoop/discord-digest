# Guide d'installation — Discord Weekly Digest → Google Doc

Ce guide te permet de mettre en place un bot Discord qui, chaque dimanche soir,
collecte automatiquement les messages de la semaine et les dépose dans un Google Doc.

Durée estimée : **30 à 45 minutes** (première fois)

---

## Vue d'ensemble

```
Bot Discord  →  Script Python  →  Google Doc
(lit les canaux)  (tourne chaque dimanche)  (mis à jour automatiquement)
```

Les 4 grandes étapes :
1. Créer le bot Discord
2. Configurer Google Cloud (accès au Google Doc)
3. Tester en local
4. Déployer sur Railway (exécution automatique chaque semaine)

---

## Étape 1 — Créer le bot Discord

### 1.1 Créer l'application

1. Va sur https://discord.com/developers/applications
2. Clique sur **New Application** (en haut à droite)
3. Donne-lui un nom (ex : `digest-hebdo`) → **Create**

### 1.2 Créer le bot

1. Dans le menu gauche, clique sur **Bot**
2. Clique sur **Add Bot** → **Yes, do it!**
3. Dans la section **Token**, clique sur **Reset Token** puis **Copy**
4. ⚠️ **Conserve ce token précieusement** — tu en auras besoin plus tard
5. Active les deux options suivantes (section *Privileged Gateway Intents*) :
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
6. Clique sur **Save Changes**

### 1.3 Inviter le bot sur ton serveur

1. Dans le menu gauche, clique sur **OAuth2** → **URL Generator**
2. Dans *Scopes*, coche : ✅ `bot`
3. Dans *Bot Permissions*, coche :
   - ✅ Read Messages/View Channels
   - ✅ Read Message History
4. Copie l'URL générée en bas de page
5. Ouvre cette URL dans ton navigateur → sélectionne ton serveur → **Autoriser**

Le bot apparaît maintenant dans ton serveur (hors ligne pour l'instant, c'est normal).

---

## Étape 2 — Configurer Google Cloud

### 2.1 Créer un projet Google Cloud

1. Va sur https://console.cloud.google.com
2. En haut, clique sur le sélecteur de projet → **Nouveau projet**
3. Nom : `discord-digest` → **Créer**
4. Assure-toi que ce projet est bien sélectionné

### 2.2 Activer l'API Google Docs

1. Dans le menu hamburger (☰) → **API et services** → **Bibliothèque**
2. Recherche `Google Docs API`
3. Clique dessus → **Activer**

### 2.3 Créer un compte de service

1. Menu (☰) → **API et services** → **Identifiants**
2. Clique sur **Créer des identifiants** → **Compte de service**
3. Nom : `discord-digest-bot` → **Créer et continuer**
4. Rôle : pas nécessaire ici → **Continuer** → **Terminer**
5. Dans la liste, clique sur le compte de service que tu viens de créer
6. Onglet **Clés** → **Ajouter une clé** → **Créer une nouvelle clé**
7. Format : **JSON** → **Créer**
8. Un fichier JSON est téléchargé — **renomme-le `credentials.json`**

### 2.4 Créer le Google Doc et le partager

1. Va sur https://docs.google.com et crée un nouveau document
2. Donne-lui un nom (ex : `Résumé Discord Hebdo`)
3. Dans l'URL, copie l'identifiant : `docs.google.com/document/d/**CECI**/edit`
4. Clique sur **Partager** (bouton en haut à droite)
5. Dans le champ email, colle l'adresse e-mail du compte de service
   (elle ressemble à `discord-digest-bot@ton-projet.iam.gserviceaccount.com`,
   tu la trouves dans le fichier `credentials.json` au champ `client_email`)
6. Donne-lui l'accès **Éditeur** → **Envoyer**

---

## Étape 3 — Tester en local

### 3.1 Prérequis

- Python 3.10 ou plus récent installé sur ta machine
- Un terminal (PowerShell, Terminal macOS, ou bash Linux)

### 3.2 Créer un environnement virtuel et installer les dépendances

Un environnement virtuel (`venv`) isole les dépendances du projet du reste de
ton système Python. C'est une bonne pratique pour éviter les conflits de versions.

```bash
# Dans le dossier discord_digest/
python -m venv venv
```

Active l'environnement :

```bash
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

Ton terminal affiche `(venv)` au début de la ligne pour confirmer que l'environnement est actif.

Installe ensuite les dépendances dans cet environnement :

```bash
pip install -r requirements.txt
```

> ℹ️ Le venv est uniquement pour les tests en local. Sur GitHub Actions, chaque
> exécution repart d'une machine vierge — le cloisonnement est déjà natif, pas
> besoin de venv dans le workflow.

### 3.3 Créer le fichier .env

Copie `.env.example` en `.env` :

```bash
cp .env.example .env
```

Ouvre `.env` et remplis les trois valeurs :

```
DISCORD_TOKEN=le_token_copié_à_l_étape_1.2
GOOGLE_DOC_ID=l_id_copié_à_l_étape_2.4
GOOGLE_CREDENTIALS_FILE=credentials.json
```

Place ton fichier `credentials.json` dans le même dossier que `bot.py`.

### 3.4 Lancer le bot une première fois

```bash
python bot.py
```

Tu devrais voir dans le terminal :
```
Bot connecté : digest-hebdo#1234
Serveur : Nom de ton serveur
  ✅ #général — 12 message(s)
  ✅ #projets — 5 message(s)
  ...
✅ Google Doc mis à jour avec succès !
```

Ouvre ton Google Doc — il doit contenir les messages de la semaine organisés par canal.

---

## Étape 4 — Déployer avec GitHub Actions (exécution automatique gratuite)

GitHub Actions exécute le script sur les serveurs de GitHub, gratuitement.
Aucun compte supplémentaire, aucune carte bancaire requise.

### 4.1 Préparer le dépôt Git

1. Crée un dépôt sur https://github.com (privé de préférence)
2. Reproduis cette structure de fichiers :

```
discord_digest/
├── .github/
│   └── workflows/
│       └── weekly_digest.yml   ← le fichier de workflow
├── bot.py
├── requirements.txt
└── .gitignore
```

3. Crée le fichier `.gitignore` avec ce contenu :

```
.env
credentials.json
venv/
__pycache__/
*.pyc
```

4. Pousse le code (⚠️ sans `.env` ni `credentials.json`) :

```bash
git add bot.py requirements.txt .gitignore .github/
git commit -m "Initial commit"
git push
```

### 4.2 Ajouter les secrets GitHub

Les informations sensibles (token Discord, credentials Google) ne sont jamais
stockées dans le code — elles sont déposées comme **secrets chiffrés** dans GitHub.

1. Sur GitHub, ouvre ton dépôt → **Settings** → **Secrets and variables** → **Actions**
2. Clique sur **New repository secret** et ajoute ces 3 secrets :

| Nom du secret | Valeur |
|---|---|
| `DISCORD_TOKEN` | Le token copié à l'étape 1.2 |
| `GOOGLE_DOC_ID` | L'ID du Google Doc copié à l'étape 2.4 |
| `GOOGLE_CREDENTIALS_JSON` | Le contenu **entier** du fichier `credentials.json` |

Pour `GOOGLE_CREDENTIALS_JSON` : ouvre `credentials.json` dans un éditeur de texte,
sélectionne tout (Ctrl+A), copie, et colle dans le champ valeur du secret.

### 4.3 Vérifier le workflow

Le fichier `.github/workflows/weekly_digest.yml` configure l'exécution automatique :
- **Déclencheur automatique** : chaque dimanche à 20h00 UTC (22h en été, 21h en hiver)
- **Déclencheur manuel** : depuis l'onglet **Actions** de ton dépôt GitHub,
  clique sur **Discord Weekly Digest** → **Run workflow** → **Run workflow**

C'est ce déclencheur manuel qui te permet de tester sans attendre le dimanche.

### 4.4 Tester le premier lancement

1. Va dans l'onglet **Actions** de ton dépôt GitHub
2. Dans la liste à gauche, clique sur **Discord Weekly Digest**
3. Bouton **Run workflow** → **Run workflow**
4. Une exécution apparaît dans la liste — clique dessus pour voir les logs en direct
5. Chaque étape doit afficher une coche verte ✅
6. Ouvre ton Google Doc pour vérifier que le contenu est bien apparu

Si une étape est rouge, clique dessus pour lire le message d'erreur
(la section Résolution de problèmes en fin de guide peut t'aider).

---

## Format du Google Doc généré

```
RÉSUMÉ DISCORD DE LA SEMAINE
Du 05/05/2025 au 12/05/2025
==================================================

#général  (8 messages)
----------------------------------------
[05/05 09:14]  Alice  :  Bonjour tout le monde !
[05/05 11:32]  Bob    :  La réunion est confirmée pour jeudi
[07/05 18:05]  Alice  :  Compte-rendu partagé dans #projets
...

#projets  (3 messages)
----------------------------------------
[07/05 18:06]  Alice  :  Voici le CR de la réunion : [lien]
...

— Généré automatiquement le 12/05/2025 à 20:00 —
```

---

## Personnalisation

Le fichier `bot.py` contient quelques constantes facilement modifiables en haut du fichier :

| Variable | Valeur par défaut | Description |
|---|---|---|
| `DAYS_BACK` | `7` | Nombre de jours en arrière à collecter |
| `SKIP_BOT_MESSAGES` | `True` | Ignorer les messages des autres bots |

Pour exclure certains canaux, ajoute dans `collect_messages()` :

```python
CANAUX_EXCLUS = {"off-topic", "blagues", "random"}

for channel in guild.text_channels:
    if channel.name in CANAUX_EXCLUS:
        continue
    # ... reste du code
```

---

## Résolution de problèmes fréquents

**"Missing Access" ou "Forbidden"**
→ Le bot n'a pas accès à ce canal. Vérifie ses permissions dans les paramètres Discord du canal.

**"Invalid token"**
→ Régénère le token dans le portail Discord Developer et mets à jour ta variable d'environnement.

**"The caller does not have permission"** (Google)
→ Vérifie que l'email du compte de service a bien été ajouté comme éditeur du Google Doc.

**Le Google Doc n'est pas mis à jour**
→ Vérifie que `GOOGLE_DOC_ID` correspond bien à l'ID dans l'URL du document.
