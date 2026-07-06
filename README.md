# Discord Weekly Digest

Bot qui collecte chaque semaine les messages Discord et les dépose automatiquement dans un Google Doc partagé (update 07/26).

**Cas d'usage :** l'ensemble de notre collectif n'est pas sur Discord — le résumé est glissé chaque lundi dans la liste de diffusion par mail.

---

## Comment ça marche

Chaque dimanche à 22h (heure française), GitHub Actions exécute le script Python qui :
1. Se connecte au serveur Discord
2. Collecte tous les messages de la semaine sur tous les canaux
3. Les organise par jour (plus récent en premier) puis par canal
4. Insère le résumé en tête du Google Doc (les semaines précédentes restent en dessous)

Le Google Doc est structuré avec des titres (Semaine → Jour → Canal) pour faciliter la navigation.

---

## Prérequis

- Un compte GitHub (pour héberger le code et exécuter le bot)
- Un serveur Discord sur lequel tu as les droits d'administrateur
- Un compte Google (pour le Google Doc de destination)

Aucune carte bancaire, aucun serveur à louer.

---

## Installation

Le guide complet pas-à-pas est dans [`GUIDE_INSTALLATION.md`](./GUIDE_INSTALLATION.md).

En résumé, il faut configurer trois choses :

**1. Le bot Discord**
Créer une application sur https://discord.com/developers/applications, générer un token, et inviter le bot sur le serveur avec les permissions de lecture des messages.

**2. Google Cloud**
Créer un compte de service sur https://console.cloud.google.com, activer l'API Google Docs, télécharger le fichier `credentials.json`, et partager le Google Doc avec l'adresse e-mail du compte de service.

**3. Les secrets GitHub**
Dans le dépôt GitHub : *Settings → Secrets and variables → Actions*, ajouter :

| Secret | Description |
|---|---|
| `DISCORD_TOKEN` | Token du bot Discord |
| `GOOGLE_DOC_ID` | ID du Google Doc (dans l'URL) |
| `GOOGLE_CREDENTIALS_JSON` | Contenu complet du fichier `credentials.json` |

---

## Tester en local

```bash
# Cloner le dépôt
git clone https://github.com/<votre-orga>/discord-digest.git
cd discord-digest

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# → Remplir DISCORD_TOKEN, GOOGLE_DOC_ID et GOOGLE_CREDENTIALS_FILE dans .env
# → Placer credentials.json dans le dossier du projet

# Lancer le bot
python bot.py
```

---

## Personnalisation

Les paramètres se trouvent en haut de `bot.py` :

| Variable | Défaut | Description |
|---|---|---|
| `DAYS_BACK` | `7` | Nombre de jours en arrière à collecter |
| `SKIP_BOT_MESSAGES` | `True` | Ignorer les messages des autres bots |
| `TIMEZONE` | `Europe/Paris` | Fuseau horaire pour l'affichage des heures |

Pour **exclure des canaux**, ajouter dans `collect_messages()` :

```python
CANAUX_EXCLUS = {"off-topic", "blagues"}

for channel in guild.text_channels:
    if channel.name in CANAUX_EXCLUS:
        continue
```

---

## Structure du projet

```
discord_digest/
├── .github/
│   └── workflows/
│       └── weekly_digest.yml   # Cron job GitHub Actions (dimanche 22h)
├── bot.py                      # Script principal
├── requirements.txt            # Dépendances Python
├── .env.example                # Template des variables d'environnement
├── README.md                   # Ce fichier
└── GUIDE_INSTALLATION.md       # Guide détaillé pas-à-pas
```

---

## Contribuer

1. Forker le dépôt ou créer une branche (`git checkout -b ma-modification`)
2. Tester en local avec `python bot.py`
3. Pousser et ouvrir une Pull Request

Pour toute question ou bug, ouvrir une issue sur le dépôt GitHub.
