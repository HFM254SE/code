"""Tests für die Lab-Werkzeuge aus VL 9: Mutation-Dojo, Spec-Gate, YAML-Leser.

Wer prüft die Prüfer? Diese Datei hält die Zahlen fest, auf die sich Lab und
Folien stützen (4 von 34 eliminiert, 26 von 34 nur mit eingefrorenem FROZEN,
8 Äquivalenz-Kandidaten, 7 Drift-Befunde), und die Design-Entscheidungen der
Werkzeuge. Die Erwartungen stehen als ausgeschriebene Literale hier, nicht aus
dem Code abgeleitet. Das ist dieselbe Entscheidung wie FROZEN in Aufgabe C.

Alle Tests laufen offline und ohne Server. Sie bleiben während des Labs grün:
Die Spec-Erweiterung aus Aufgabe D fügt nur Befunde hinzu und nimmt keine weg.
Keine pytest-Fixtures, damit auch `mutation_dojo.py --tests` die Datei ausführen
kann.
"""

import ast
import tempfile
from pathlib import Path

from src import triage
from tools import mutation_dojo, spec_gate, specyaml

REPO = Path(__file__).resolve().parent.parent

# Eingefrorenes Orakel: die acht Mutanten, die keine Eingabe unterscheiden kann.
# Sieben Software-Keywords (Software ist letzte Kategorie UND Default) und
# `wlan` (jeder Text mit "wlan" enthält auch "lan").
AEQUIVALENZ_KANDIDATEN = {
    "Software/absturz", "Software/fehlermeldung", "Software/update",
    "Software/installation", "Software/lizenz", "Software/programm",
    "Software/anwendung", "Netzwerk/wlan",
}

# Eingefrorenes Orakel: die sieben Befunde des Gates auf dem Drift-Server.
DRIFT_BEFUNDE = {
    ("ERRCODE", "GET /tickets/{ticket_id}"),
    ("EXTRA", "GET /health"),
    ("QPARAM", "GET /tickets"),
    ("ROUTE", "POST /tickets/{ticket_id}/escalate"),
    ("SCHEMA", "GET /tickets/{ticket_id}"),
    ("SCHEMA", "POST /tickets"),
    ("SCHEMA", "POST /tickets/{ticket_id}/triage"),
}


# ---------------------------------------------------------------------------
# Mutation-Dojo
# ---------------------------------------------------------------------------

def test_ausgelieferte_suite_eliminiert_genau_vier_von_34():
    suite, fehler = mutation_dojo.build_suite("shipped")
    assert fehler is None
    mutanten = mutation_dojo.mutants_for("category")
    eliminiert, _ = mutation_dojo.messen(suite, mutanten)
    assert len(mutanten) == 34
    assert set(eliminiert) == {"Hardware/drucker", "Hardware/laptop",
                               "Netzwerk/vpn", "Zugang/zugriff"}


def test_mutant_setzt_die_tabelle_auch_nach_einer_exception_zurueck():
    vorher = {row: list(kws) for row, kws in triage.CATEGORY_KEYWORDS.items()}
    try:
        with mutation_dojo.mutant("Zugang", "passwort"):
            assert "passwort" not in triage.CATEGORY_KEYWORDS["Zugang"]
            raise RuntimeError("Abbruch mitten im Lauf")
    except RuntimeError:
        pass
    with mutation_dojo.key_mutant("Software"):
        assert "Software" not in triage.CATEGORY_KEYWORDS
    assert triage.CATEGORY_KEYWORDS == vorher
    assert list(triage.CATEGORY_KEYWORDS) == list(vorher)  # Reihenfolge zählt


def test_aequivalenz_suche_vergleicht_auch_die_prioritaet():
    # Regressionstest: Früher verglich die Suche nur die Kategorie und hielt
    # damit jeden Prioritäts-Mutanten für äquivalent.
    eingabe, original, mutant, _ = mutation_dojo.find_distinguishing_input(
        "niedrig", "frage")
    assert eingabe is not None
    assert original[1] == "niedrig"
    assert mutant[1] == "mittel"


def test_genau_acht_aequivalenz_kandidaten_in_beiden_scopes():
    for scope in ("category", "all"):
        kandidaten = set()
        for row, kw in mutation_dojo.mutants_for(scope):
            eingabe, *_ = mutation_dojo.find_distinguishing_input(
                row, kw, mutation_dojo.ZUSATZ_KANDIDATEN)
            if eingabe is None:
                kandidaten.add(f"{row}/{kw}")
        assert kandidaten == AEQUIVALENZ_KANDIDATEN, scope


_FROZEN_TESTDATEI = (
    "from src.triage import CATEGORY_KEYWORDS, classify_and_prioritize\n\n"
    "{frozen}\n\n"
    "def test_jedes_keyword_trifft_seine_kategorie_eingefroren():\n"
    "    for kategorie, keywords in FROZEN.items():\n"
    "        for keyword in keywords:\n"
    "            ticket = {{'betreff': keyword, 'text': keyword}}\n"
    "            assert classify_and_prioritize(ticket)[0] == kategorie\n"
)


def _eliminiert_mit_frozen(frozen_zeile: str) -> int:
    """Misst `--suite frozen` für eine Testdatei, in der FROZEN so definiert ist."""
    with tempfile.TemporaryDirectory() as ordner:
        pfad = Path(ordner) / "test_triage_oracle.py"
        pfad.write_text(_FROZEN_TESTDATEI.format(frozen=frozen_zeile), encoding="utf-8")
        suite, fehler = mutation_dojo.build_suite("frozen", pfad)
        assert fehler is None
        assert suite() == []  # auf dem intakten Modul grün
        eliminiert, _ = mutation_dojo.messen(suite, mutation_dojo.mutants_for("category"))
        return len(eliminiert)


def test_dojo_laedt_die_testdatei_pro_mutant_neu():
    # Regressionstest: Früher lud der Dojo die Testdatei einmal VOR den
    # Mutanten. Eine Ableitung auf Modulebene lief dann mit der intakten
    # Tabelle und ergab 26 von 34 wie ein Literal. Bei einer echten Änderung
    # in src/triage.py wandert sie aber mit und eliminiert nichts.
    abgeleitet = "FROZEN = {k: tuple(v) for k, v in CATEGORY_KEYWORDS.items()}"
    literal = f"FROZEN = {({k: tuple(v) for k, v in triage.CATEGORY_KEYWORDS.items()})!r}"
    assert _eliminiert_mit_frozen(abgeleitet) == 0
    assert _eliminiert_mit_frozen(literal) == 26


def test_leerer_testrumpf_wird_erkannt():
    quelltext = (
        "def test_leer():\n    ...\n\n"
        "def test_nur_docstring():\n    \"\"\"Kommt noch.\"\"\"\n    pass\n\n"
        "def test_voll():\n    assert 1 + 1 == 2\n"
    )
    with tempfile.TemporaryDirectory() as ordner:
        pfad = Path(ordner) / "test_beispiel.py"
        pfad.write_text(quelltext, encoding="utf-8")
        assert mutation_dojo.leerer_test(pfad, "test_leer")
        assert mutation_dojo.leerer_test(pfad, "test_nur_docstring")
        assert not mutation_dojo.leerer_test(pfad, "test_voll")
        assert mutation_dojo.leerer_test(pfad, "test_gibt_es_nicht")


# ---------------------------------------------------------------------------
# Spec-Gate
# ---------------------------------------------------------------------------

def test_gate_findet_alle_sieben_drifts():
    befunde = {(b.art, b.ort) for b in spec_gate.gate(REPO / "api" / "drifted_server.py")}
    assert DRIFT_BEFUNDE <= befunde


def test_gate_meldet_auf_der_referenz_hoechstens_fehlende_routen():
    # Zwischen Aufgabe D und E fehlt der neue Handler noch (1 ROUTE-Befund).
    # Jede andere Befundart auf app.py wäre ein Fehlalarm oder echter Drift.
    befunde = spec_gate.gate(REPO / "api" / "app.py")
    assert [str(b) for b in befunde if b.art != "ROUTE"] == []


def _modell(quelltext: str) -> tuple[dict, dict]:
    tree = ast.parse(quelltext)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    return functions, classes


def test_gate_zaehlt_pydantic_body_modelle_nicht_als_query_parameter():
    functions, classes = _modell(
        "class Basis(BaseModel):\n    grund: str\n\n"
        "class Kind(Basis):\n    extra: str\n\n"
        "class KategorieEnum(str, Enum):\n    Hardware = 'Hardware'\n\n"
        "@app.post('/tickets/{ticket_id}/notiz')\n"
        "def notiz(ticket_id: str, eingabe: Kind, kategorie: KategorieEnum | None = None):\n"
        "    ...\n"
    )
    assert spec_gate._query_params(functions["notiz"], classes) == {"kategorie"}


def test_gate_verfolgt_statuscodes_in_hilfsfunktionen():
    functions, _ = _modell(
        "def _require(ticket_id):\n"
        "    raise HTTPException(status_code=404, detail='fehlt')\n\n"
        "def handler(ticket_id):\n"
        "    return _require(ticket_id)\n"
    )
    assert spec_gate._raised_status_codes(functions["handler"], functions, set()) == {404}


# ---------------------------------------------------------------------------
# YAML-Leser
# ---------------------------------------------------------------------------

def _lade(yaml_text: str):
    with tempfile.TemporaryDirectory() as ordner:
        pfad = Path(ordner) / "spec.yaml"
        pfad.write_text(yaml_text, encoding="utf-8")
        return specyaml.load(pfad)


def test_specyaml_liest_blockstil_inline_listen_und_leere_map():
    spec = _lade(
        "schemas:\n"
        "  Report:\n"
        "    type: object\n"
        "    required: [gesamt, kategorien]\n"
        "    properties:\n"
        "      gesamt:\n"
        "        type: integer\n"
        "        minimum: 0\n"
        "      egal: {}\n"
    )
    report = spec["schemas"]["Report"]
    assert report["required"] == ["gesamt", "kategorien"]
    assert report["properties"]["gesamt"] == {"type": "integer", "minimum": 0}
    assert report["properties"]["egal"] == {}


def test_specyaml_bricht_bei_flow_maps_mit_zeilennummer_ab():
    faelle = [
        ("gesamt:\n  schema: { type: integer }\n", "Zeile 2"),
        # Nach dem Ende eines gefalteten Blocks wird wieder geprüft.
        ("info:\n  description: >\n    Freitext\n  schema: { type: integer }\n", "Zeile 4"),
    ]
    for yaml_text, zeile in faelle:
        try:
            _lade(yaml_text)
        except specyaml.SpecYamlFehler as fehler:
            assert zeile in str(fehler)
        else:
            raise AssertionError(f"Flow-Map wurde still akzeptiert: {yaml_text!r}")


def test_specyaml_liest_klammern_im_gefalteten_block_als_text():
    spec = _lade(
        "info:\n"
        "  description: >\n"
        "    Beispiel: {gesamt: 30}\n"
        "    zweite Zeile\n"
        "  leer: { }\n"
    )
    assert spec["info"]["description"] == "Beispiel: {gesamt: 30} zweite Zeile"
    assert spec["info"]["leer"] == {}


def test_specyaml_loest_ref_bewusst_nicht_auf():
    spec = specyaml.load(REPO / "api" / "openapi.yaml")
    schema = spec["paths"]["/tickets/{ticket_id}"]["get"]["responses"]["200"][
        "content"]["application/json"]["schema"]
    assert schema == {"$ref": "#/components/schemas/Ticket"}
