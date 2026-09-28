"""Gemeinsame pytest-Konfiguration aller Checkpoints (liegt im Repo-Wurzelverzeichnis).

1. Import-Pfad: Beim Laden legt pytest das Verzeichnis dieser Datei in sys.path
   (Import-Modus "prepend", der Default). Deshalb funktionieren
   `from src.triage import ...` und ab VL 9 `from tools import specyaml` in
   tests/ ohne Installation. Das bewirkt schon die bloße Anwesenheit der Datei.

2. Ruhige Testausgabe: Bibliotheken wie litellm oder pydantic melden beim Import
   Deprecation-Warnungen, die nichts mit dem Kurs-Code zu tun haben. Die Filter
   unten blenden solche Warnungen aus fremden Paketen aus. Warnungen aus dem
   eigenen Code (src/, api/, tools/ und die Tests) bleiben sichtbar.
"""

import warnings

import pytest

# Wie Zeilen unter `filterwarnings` in einer pytest.ini. Spätere Zeilen haben
# Vorrang, deshalb stehen die Ausnahmen für den eigenen Code am Ende.
WARNUNGSFILTER = (
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
    r"default::DeprecationWarning:(src|api|tools)\.",
    "default::DeprecationWarning:test_",  # Testmodule heißen ohne Paketnamen test_…
)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Trägt die Filter ein, bevor andere Plugins starten."""
    for zeile in WARNUNGSFILTER:
        config.addinivalue_line("filterwarnings", zeile)
    # pytest-asyncio (nicht in requirements.txt, aber oft global installiert)
    # warnt schon beim Start über eine fehlende Einstellung. Dieser Filter gilt
    # nur, solange pytest die Plugins startet.
    warnings.filterwarnings(
        "ignore", message='The configuration option "asyncio_default_fixture_loop_scope"'
    )
