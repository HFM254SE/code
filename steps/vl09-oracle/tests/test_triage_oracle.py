"""Datengetriebene Tests für die Triage-Keywords. GERÜST mit drei TODOs.

Wird in Teil 1 des Labs gefüllt. Absichtlich eine schlichte Schleife statt
`@pytest.mark.parametrize`: So läuft dieselbe Datei unter pytest UND unter
tools/mutation_dojo.py. Der Dojo führt genau die Tests aus, die ihr hier
schreibt. Er hat keine eigene Kopie davon.

Deshalb: **die drei Funktionsnamen bitte nicht umbenennen.** Der Dojo sucht
sie namentlich. Ein umbenannter Test gilt ihm als ungefüllt.

Achtung, Orakel-Falle im Werkzeug: Solange ein Rumpf nur `...` enthält,
meldet pytest den Test als "passed". Der Dojo meldet ihn als "leer".

Ausführen:
    python3 tools/mutation_dojo.py --suite oracle                      # TODO 1
    python3 tools/mutation_dojo.py --suite frozen                      # TODO 2
    python3 tools/mutation_dojo.py --tests tests/test_triage_oracle.py # alle drei
"""

from src.triage import CATEGORY_KEYWORDS, classify_and_prioritize  # noqa: F401 (für die TODOs)


def _ticket(betreff: str, text: str) -> dict:
    return {"id": "T-9999", "von": "test@leinetech.de", "betreff": betreff,
            "text": text, "erstellt": "2026-05-01"}


# ---------------------------------------------------------------------------
# TODO 1: Der naheliegende Weg (Lab, Aufgabe B)
#
# Schreibt EINEN Test, der über alle Keywords läuft und prüft, dass jedes
# Keyword seiner Kategorie zugeordnet wird. Nutzt dafür CATEGORY_KEYWORDS,
# also die Tabelle aus dem Modul. Keine Magic Strings, kein Duplikat: Das ist
# die Refaktorierung, die man in jedem Review vorschlagen würde.
#
# Anforderungen:
#   1. eine Schleife über CATEGORY_KEYWORDS.items()
#   2. pro Keyword ein Ticket bauen (betreff = text = Keyword)
#   3. assert kategorie == erwartete Kategorie
#
# NOTIERT DIE ZAHL, die --suite oracle danach ausgibt, BEVOR ihr weiterlest.
# ---------------------------------------------------------------------------

def test_jedes_keyword_trifft_seine_kategorie():
    ...  # TODO 1: Rumpf ersetzen


# ---------------------------------------------------------------------------
# TODO 2: Derselbe Test, eine Zeile anders (Lab, Aufgabe C)
#
# Kopiert den Test von oben. Ändert genau EINE Sache: Die Erwartung kommt
# nicht mehr aus dem Modul, sondern aus einer eingefrorenen Kopie der Tabelle,
# die HIER in dieser Datei steht.
#
# Anforderungen:
#   1. FROZEN als dict[str, tuple[str, ...]] hier im Testmodul anlegen, und
#      zwar als ausgeschriebenes Literal, NICHT aus CATEGORY_KEYWORDS
#      abgeleitet (eine Ableitung wäre wieder dasselbe mitwandernde Orakel)
#   2. sonst identische Schleife und identische Assertion
#   3. Zahl aus --suite frozen mit der aus TODO 1 vergleichen
#
# Ja, das dupliziert Daten. Notiert im Kommentar, WARUM das hier richtig ist.
# ---------------------------------------------------------------------------

FROZEN: dict[str, tuple[str, ...]] = {}  # TODO 2: Tabelle eintragen


def test_jedes_keyword_trifft_seine_kategorie_eingefroren():
    ...  # TODO 2: Rumpf ersetzen


# ---------------------------------------------------------------------------
# TODO 3: Die ehrliche Grenze (Lab, Für zu Hause)
#
# Beide Tests oben setzen betreff UND text auf dasselbe Keyword. Baut
# dieselbe Schleife noch einmal, aber diesmal steht das Keyword NUR im
# Betreff. Als Text nehmt ihr einen festen Platzhalter ohne Keyword, z. B.
# "kein inhalt". Erwartung ist weiterhin FROZEN.
#
# Laufen lassen:
#   python3 tools/mutation_dojo.py --tests tests/test_triage_oracle.py
#
# Was ihr sehen werdet: Der Test ist grün, alle 34 Fälle bestehen. Er
# findet also NICHTS, was die beiden Tests oben nicht schon gefunden hätten.
#
# Notiert im Kommentar, warum: Welche Felder liest _ticket_text(), und was
# heißt das für die Eingabemenge, gegen die wir den Score gemessen haben?
# (Stichwort: mehr Testfälle sind nicht dasselbe wie mehr Orakel. Diese
# Variation ändert die Eingabe nicht entlang einer Dimension, auf die der
# Prüfling überhaupt reagiert.)
# ---------------------------------------------------------------------------

def test_keyword_nur_im_betreff():
    ...  # TODO 3: Rumpf ersetzen
