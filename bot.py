"""
Discord Weekly Digest → Google Doc
Collecte les messages de la semaine passée sur tous les canaux Discord
et met à jour un Google Doc avec un résumé organisé par jour (décroissant) puis par canal,
avec des niveaux de titre Google Docs (H1 semaine, H2 jour, H3 canal).

Lancer ce script chaque dimanche soir (cron job sur GitHub Actions).
"""

from __future__ import annotations

import asyncio
import logging
import os
import warnings
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import discord
import pytz
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Supprimer les erreurs bénignes de fermeture SSL/aiohttp sur Python 3.8
warnings.filterwarnings("ignore", category=ResourceWarning)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

load_dotenv()

DISCORD_TOKEN   = os.getenv("DISCORD_TOKEN")
GOOGLE_DOC_ID   = os.getenv("GOOGLE_DOC_ID")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

DAYS_BACK          = 7
SKIP_BOT_MESSAGES  = True
TIMEZONE           = pytz.timezone("Europe/Paris")

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR  = ["janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

# Couleur grise pour les lignes de contexte de réponse
GREY = {"red": 0.6, "green": 0.6, "blue": 0.6}


def utf16_len(s: str) -> int:
    """Nombre d'unités de code UTF-16 utilisé par l'API Google Docs pour les positions."""
    return len(s.encode("utf-16-le")) // 2


def format_day_fr(day) -> str:
    return f"{JOURS_FR[day.weekday()]} {day.day} {MOIS_FR[day.month - 1]} {day.year}"


def to_local(ts_utc: datetime) -> datetime:
    return ts_utc.astimezone(TIMEZONE)


def resolve_mentions(msg: discord.Message) -> str:
    """
    Remplace les mentions brutes Discord (<@ID>, <#ID>, <@&ID>)
    par leurs noms lisibles. discord.py pré-résout déjà les objets
    dans msg.mentions, msg.channel_mentions et msg.role_mentions.
    """
    content = msg.content
    for user in msg.mentions:
        content = content.replace(f"<@{user.id}>",  f"@{user.display_name}")
        content = content.replace(f"<@!{user.id}>", f"@{user.display_name}")
    for channel in msg.channel_mentions:
        content = content.replace(f"<#{channel.id}>", f"#{channel.name}")
    for role in msg.role_mentions:
        content = content.replace(f"<@&{role.id}>", f"@{role.name}")
    return content


# ---------------------------------------------------------------------------
# Collecte des messages Discord
# ---------------------------------------------------------------------------

async def collect_messages(client: discord.Client) -> dict[str, list[dict]]:
    since  = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
    result = {}

    for guild in client.guilds:
        print(f"Serveur : {guild.name}")
        for channel in guild.text_channels:
            messages = []
            try:
                async for msg in channel.history(after=since, oldest_first=True, limit=None):
                    if SKIP_BOT_MESSAGES and msg.author.bot:
                        continue
                    if not msg.content.strip():
                        continue

                    # Contexte de réponse
                    reply_context = None
                    if msg.reference:
                        try:
                            if msg.reference.resolved and isinstance(msg.reference.resolved, discord.Message):
                                ref = msg.reference.resolved
                            else:
                                ref = await channel.fetch_message(msg.reference.message_id)
                            excerpt = resolve_mentions(ref).replace("\n", " ")
                            if len(excerpt) > 150:
                                excerpt = excerpt[:147] + "..."
                            reply_context = {"author": ref.author.display_name, "content": excerpt}
                        except (discord.NotFound, discord.HTTPException):
                            reply_context = {"author": "?", "content": "[message supprimé]"}

                    messages.append({
                        "timestamp":     msg.created_at,
                        "author":        msg.author.display_name,
                        "content":       resolve_mentions(msg),
                        "reply_context": reply_context,
                    })

            except discord.Forbidden:
                print(f"  ⚠️  Accès refusé : #{channel.name}")
                continue
            except discord.HTTPException as e:
                print(f"  ⚠️  Erreur HTTP sur #{channel.name} : {e}")
                continue

            if messages:
                result[channel.name] = messages
                print(f"  ✅ #{channel.name} — {len(messages)} message(s)")
            else:
                print(f"  —  #{channel.name} — aucun message cette semaine")

    return result


# ---------------------------------------------------------------------------
# Construction des segments
# ---------------------------------------------------------------------------
# Chaque segment est un tuple :
#   (text, para_style, bold_ranges, italic, grey, space_above_pt)
#
# • para_style    : "HEADING_1" | "HEADING_2" | "HEADING_3" | "NORMAL_TEXT"
# • bold_ranges   : [(rel_start_utf16, rel_end_utf16), ...] dans `text`
# • italic        : bool — toute la ligne en italique
# • grey          : bool — toute la ligne en gris
# • space_above_pt: int  — espace avant le paragraphe en points (0 = aucun)

def build_segments(messages_by_channel: dict) -> list[tuple]:
    now        = datetime.now(TIMEZONE)
    week_start = now - timedelta(days=DAYS_BACK)

    segs = []

    # H1 — titre de la semaine
    segs.append((
        f"Semaine du {week_start.strftime('%d/%m/%Y')} au {now.strftime('%d/%m/%Y')}",
        "HEADING_1", [], False, False, 0
    ))

    if not messages_by_channel:
        segs.append(("Aucun message cette semaine.", "NORMAL_TEXT", [], False, False, 0))
        segs.append(("", "NORMAL_TEXT", [], False, False, 0))
        segs.append(("", "NORMAL_TEXT", [], False, False, 0))
        return segs

    # Regrouper par jour local puis par canal
    by_day: dict = defaultdict(lambda: defaultdict(list))
    for canal, messages in messages_by_channel.items():
        for msg in messages:
            day = to_local(msg["timestamp"]).date()
            by_day[day][canal].append(msg)

    for day in sorted(by_day.keys(), reverse=True):
        # H2 — jour
        segs.append((format_day_fr(day), "HEADING_2", [], False, False, 0))

        for canal, messages in by_day[day].items():
            count = len(messages)
            # H3 — canal
            segs.append((
                f"#{canal}  ({count} message{'s' if count > 1 else ''})",
                "HEADING_3", [], False, False, 0
            ))

            for msg in messages:
                ts      = to_local(msg["timestamp"]).strftime("%H:%M")
                content = msg["content"].replace("\n", " ")
                if len(content) > 500:
                    content = content[:497] + "..."

                prefix = f"[{ts}]  "
                author = msg["author"]
                suffix = f"  :  {content}"
                line   = prefix + author + suffix

                author_start = utf16_len(prefix)
                author_end   = author_start + utf16_len(author)

                if msg["reply_context"]:
                    rc = msg["reply_context"]
                    # L'espace est avant le contexte (qui reste groupé avec la réponse)
                    segs.append((
                        f"  ↩ {rc['author']} : {rc['content']}",
                        "NORMAL_TEXT", [], True, True, 6   # espace avant le contexte
                    ))
                    # La réponse elle-même suit sans espace (groupée avec le contexte)
                    segs.append((line, "NORMAL_TEXT", [(author_start, author_end)], False, False, 0))
                else:
                    # Message simple : espace avant
                    segs.append((line, "NORMAL_TEXT", [(author_start, author_end)], False, False, 6))

            #segs.append(("", "NORMAL_TEXT", [], False, False, 0))   # ligne vide entre canaux

    segs.append((
        f"— Généré automatiquement le {now.strftime('%d/%m/%Y à %H:%M')} —",
        "NORMAL_TEXT", [], False, False, 0
    ))
    segs.append(("", "NORMAL_TEXT", [], False, False, 0))
    segs.append(("", "NORMAL_TEXT", [], False, False, 0))

    return segs


# ---------------------------------------------------------------------------
# Mise à jour du Google Doc
# ---------------------------------------------------------------------------

def update_google_doc(segments: list[tuple]) -> None:
    scopes  = ["https://www.googleapis.com/auth/documents"]
    creds   = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    service = build("docs", "v1", credentials=creds)

    full_text = ""
    requests  = []

    # On collecte d'abord les infos de position pour chaque segment
    seg_positions = []
    for text, para_style, bold_ranges, italic, grey, space_above_pt in segments:
        line       = text + "\n"
        line_start = utf16_len(full_text) + 1
        line_end   = line_start + utf16_len(line)
        text_end   = line_start + utf16_len(text)   # sans le \n final
        seg_positions.append((line_start, line_end, text_end,
                               para_style, bold_ranges, italic, grey, space_above_pt))
        full_text += line

    # 1. Insérer tout le texte en tête de document
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": full_text,
        }
    })

    # 2. Styles de paragraphe — TOUS les paragraphes sont explicitement stylisés
    #    (évite l'héritage du style H1 de la semaine précédente à l'index 1)
    for line_start, line_end, text_end, para_style, _, _, _, space_above_pt in seg_positions:
        if para_style in ("HEADING_1", "HEADING_2", "HEADING_3"):
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": line_start, "endIndex": line_end},
                    "paragraphStyle": {"namedStyleType": para_style},
                    "fields": "namedStyleType",
                }
            })
        else:
            # NORMAL_TEXT explicite + espacement optionnel
            para_style_obj = {"namedStyleType": "NORMAL_TEXT"}
            fields = "namedStyleType"
            if space_above_pt > 0:
                para_style_obj["spaceAbove"] = {"magnitude": space_above_pt, "unit": "PT"}
                fields += ",spaceAbove"
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": line_start, "endIndex": line_end},
                    "paragraphStyle": para_style_obj,
                    "fields": fields,
                }
            })

    # 3. Gras sur les noms d'auteurs
    for line_start, _, _, _, bold_ranges, _, _, _ in seg_positions:
        for rel_s, rel_e in bold_ranges:
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": line_start + rel_s, "endIndex": line_start + rel_e},
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            })

    # 4. Italique + gris sur les lignes de contexte de réponse
    for line_start, _, text_end, _, _, italic, grey, _ in seg_positions:
        if not (italic or grey):
            continue
        text_style = {}
        fields_ts  = []
        if italic:
            text_style["italic"] = True
            fields_ts.append("italic")
        if grey:
            text_style["foregroundColor"] = {"color": {"rgbColor": GREY}}
            fields_ts.append("foregroundColor")
        requests.append({
            "updateTextStyle": {
                "range": {"startIndex": line_start, "endIndex": text_end},
                "textStyle": text_style,
                "fields": ",".join(fields_ts),
            }
        })

    service.documents().batchUpdate(
        documentId=GOOGLE_DOC_ID,
        body={"requests": requests},
    ).execute()

    print("✅ Google Doc mis à jour avec succès !")


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

async def main() -> None:
    # Supprimer les erreurs SSL bénignes liées à la fermeture d'aiohttp sur Python 3.8
    loop = asyncio.get_event_loop()

    def suppress_ssl_close_errors(loop, context):
        exc = context.get("exception")
        msg = context.get("message", "")
        if "SSL" in msg or isinstance(exc, (OSError, RuntimeError)):
            return  # ignorer silencieusement
        loop.default_exception_handler(context)

    loop.set_exception_handler(suppress_ssl_close_errors)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Bot connecté : {client.user}")
        try:
            messages_by_channel = await collect_messages(client)
            segments = build_segments(messages_by_channel)
            update_google_doc(segments)
        finally:
            await asyncio.sleep(0.5)
            await client.close()

    async with client:
        await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
