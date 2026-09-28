"""RAG-Evaluation: misst Retrieval und Antworten auf dem Evalset eval/rag_eval.jsonl.

Zwei Stufen:

    --retrieval-only     nur Retrieval, keine Chat-Aufrufe (Lab Teil 2, dauert Sekunden)
      Datei-Treffer      Steht ein Chunk aus der erwarteten Datei in den Top-k?
      Beleg-Treffer      Stehen alle Belegstellen (Feld "evidence") in abgerufenen
                         Chunks der erwarteten Datei? Das ist eine grobe,
                         deterministische Näherung an Context Recall.

    ohne Schalter        zusätzlich Antworten erzeugen und bewerten (Lab-Vertiefung)
                         Die beiden Judge-Funktionen sind hier noch TODO (V1, V2).
                         Bis dahin zeigt der Report "–" statt einer Zahl.
      Enthaltung         korrekt bei unbeantwortbaren, fälschlich bei beantwortbaren Fragen
      Faithfulness       Anteil der Aussagen, die der Kontext stützt (LLM-as-a-Judge)
      Answer Relevancy   Wie direkt beantwortet die Antwort die Frage? (LLM-as-a-Judge)

Der Datei-Treffer kann täuschen: Die Hotline (-4242) und die Durchwahl von Bernd
Hagedorn (-4200) stehen in derselben Datei. Deshalb zählt der Beleg-Treffer die
konkrete Belegstelle. Er zählt sie nur in Chunks der erwarteten Datei, denn
Ablenker aus anderen Dateien enthalten oft dieselbe Zeichenfolge: "2 Stunden"
steht auch bei den Leihgeräten in hardware-bestellung.md, nicht nur in der
SLA-Tabelle.

Die Judge-Werte sind Richtungssignale zum Vergleich von Konfigurationen, keine
absolute Wahrheit. Hier bewertet das Kursmodell seine eigenen Antworten
(Selbstverstärkungsbias). Bei wenigen Fragen verschiebt jede einzelne Frage das
Ergebnis deutlich. Deshalb berichtet der Report Zählungen.

Aufruf:
    python -m src.rag_eval --retrieval-only --retriever keyword --n 3
    python -m src.rag_eval --retrieval-only --retriever hybrid --n 3
    python -m src.rag_eval --retriever hybrid --n 3              # mit Antworten und Judge
    python -m src.rag_eval --retriever hybrid --n 3 --details    # plus Einzelurteile
"""

import argparse
import json
import re
from pathlib import Path

from src.llm import chat  # noqa: F401  (für TODO V1 und V2)
from src.rag import ABSTENTION, RETRIEVER_NAMES, answer, resolve_retriever
from src.vectorstore import DEFAULT_COLLECTION, create_collection

EVAL_PATH = Path("eval/rag_eval.jsonl")
UNANSWERABLE = "unbeantwortbar"
QUESTION_TYPES = ("einfach", "schwer", "keyword", UNANSWERABLE)


def load_evalset(path: Path = EVAL_PATH) -> list[dict]:
    """Lädt das Evalset: eine JSON-Zeile pro Frage, leere Zeilen werden übersprungen."""
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def is_unanswerable(entry: dict) -> bool:
    """Unbeantwortbar heißt: Typ "unbeantwortbar" oder keine erwartete Quelle."""
    return entry.get("type") == UNANSWERABLE or entry.get("expected_source") is None


# --- Retrieval: Datei-Treffer und Beleg-Treffer -----------------------------


def normalize(text: str) -> str:
    """Kleinschreibung, ohne Markdown-Hervorhebung (* und `), Leerraum vereinheitlicht."""
    text = text.lower().replace("*", "").replace("`", "")
    return " ".join(text.split())


def contains_evidence(text: str, evidence: str) -> bool:
    """Steht die Belegstelle im Text? Es zählen nur ganze Wörter.

    So passt "2 Stunden" nicht auf "12 Stunden", aber "-4242" auf "**-4242**".
    """
    pattern = r"(?<!\w)" + re.escape(normalize(evidence)) + r"(?!\w)"
    return re.search(pattern, normalize(text)) is not None


def count_evidence(evidence: list[str], hits: list[dict]) -> int:
    """Wie viele Belegstellen stehen in mindestens einem der Treffer?"""
    return sum(
        any(contains_evidence(hit["text"], literal) for hit in hits) for literal in evidence
    )


def source_hit(expected_source: str, hits: list[dict]) -> bool:
    """Datei-Treffer: Stammt mindestens ein Treffer aus der erwarteten Datei?"""
    return any(hit["source"] == expected_source for hit in hits)


# --- Antworten: Enthaltung ---------------------------------------------------

# Rückfall, falls das Modell den festen Wortlaut leicht abwandelt.
_ABSTENTION_HINTS = ("keine information", "nicht in der wissensbasis", "nicht im kontext")


def is_abstention(rag_answer: str) -> bool:
    """Hat sich das System enthalten?

    Zuerst zählt der feste Wortlaut ABSTENTION aus src/rag.py (String-Vergleich).
    Danach greifen typische Abwandlungen wie "keine Informationen".
    """
    text = normalize(rag_answer)
    if normalize(ABSTENTION).rstrip(".") in text:
        return True
    return any(hint in text for hint in _ABSTENTION_HINTS)


# --- Judge: Faithfulness und Answer Relevancy (Lab-Vertiefung, TODO V1 und V2)

JUDGE_SYSTEM = "Du bist ein strenger, präziser Bewerter. Antworte ausschließlich mit JSON."

# Reasoning-Modelle stellen ihrer Antwort manchmal einen Denkblock voran.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def parse_json_object(raw: str) -> dict | None:
    """Liest das JSON-Objekt aus einer Judge-Antwort, sonst None.

    Denkblöcke (<think>…</think>) werden entfernt. Gelesen wird von der ersten
    öffnenden bis zur letzten schließenden geschweiften Klammer. Codeblock-Zäune
    und Begleitsätze drumherum stören deshalb nicht.
    """
    text = _THINK_BLOCK.sub("", raw)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def judge_claims(question: str, rag_answer: str, context: str) -> list[dict] | None:
    """Lässt den Judge die Antwort in Aussagen zerlegen und jede einzeln prüfen.

    Gibt [{"aussage": "...", "gestützt": True}, ...] zurück. Nicht bewertbar (None)
    ist die Judge-Antwort, wenn das JSON fehlt, die Liste leer ist oder auch nur
    eine Aussage bei "gestützt" keinen Wahrheitswert (true/false) hat.
    """
    # TODO V1 (Vertiefung): Faithfulness-Judge bauen.
    #   a) Prompt schreiben, der FRAGE, KONTEXT und ANTWORT enthält und verlangt:
    #      Antwort in einzelne Aussagen zerlegen, jede Aussage einzeln gegen den
    #      Kontext prüfen, NUR JSON ausgeben in der Form
    #      {"aussagen": [{"aussage": "...", "gestützt": true}]}
    #   b) raw = chat(prompt, system=JUDGE_SYSTEM, temperature=0.0)
    #   c) data = parse_json_object(raw) und die Liste data["aussagen"] zurückgeben.
    #   d) None zurückgeben ("nicht bewertbar"), wenn das JSON fehlt, die Liste leer
    #      ist oder auch nur eine Aussage bei "gestützt" keinen bool hat (z. B.
    #      "teilweise"). Solche Aussagen wegzulassen würde die Quote schönen.
    return None


def supported_share(claims: list[dict] | None) -> float | None:
    """Anteil der gestützten Aussagen. Python rechnet, nicht das Modell."""
    if not claims:
        return None
    return sum(claim["gestützt"] for claim in claims) / len(claims)


def faithfulness(question: str, rag_answer: str, context: str) -> float | None:
    """Faithfulness: Anteil der Aussagen der Antwort, die der Kontext stützt.

    Vereinfachte Form des RAGAS-Verfahrens. RAGAS braucht zwei Aufrufe: einen zum
    Zerlegen der Antwort in Aussagen und einen zum Prüfen jeder Aussage. Hier
    erledigt ein Aufruf beides. Gleich bleibt: Das Modell urteilt pro Aussage,
    die Quote rechnet Python.
    """
    return supported_share(judge_claims(question, rag_answer, context))


def parse_score(raw: str) -> float | None:
    """Liest den Wert "relevanz" aus der Judge-Antwort, sonst None.

    Ersatzweise gilt eine Antwort, die nur aus einer Zahl besteht. Werte
    außerhalb von [0, 1] und Zahlen in Begleittext ergeben None. So wird aus
    "3/4 Aussagen, also 0.75" nicht versehentlich eine 3 oder eine 1.
    """
    data = parse_json_object(raw)
    if data is not None:
        value = data.get("relevanz")
    else:
        value = _THINK_BLOCK.sub("", raw).strip().replace(",", ".")
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if 0.0 <= score <= 1.0 else None


def answer_relevancy(question: str, rag_answer: str) -> float | None:
    """Answer Relevancy: Wie direkt beantwortet die Antwort die Frage?

    Direkter Judge. RAGAS erzeugt stattdessen Fragen aus der Antwort und
    vergleicht sie per Embedding mit der Originalfrage. Vollständigkeit prüft
    dieser Judge nicht, denn dafür bräuchte er die Referenzantwort (ground_truth).
    """
    # TODO V2 (Vertiefung): Relevanz-Judge bauen.
    #   a) Prompt mit FRAGE und ANTWORT: "Wie direkt beantwortet die ANTWORT die FRAGE?
    #      0 heißt gar nicht, 1 heißt direkt." und NUR JSON verlangen: {"relevanz": 0.8}
    #   b) raw = chat(prompt, system=JUDGE_SYSTEM, temperature=0.0)
    #   c) return parse_score(raw)
    return None


# --- Ablauf -----------------------------------------------------------------


def evaluate_entry(
    entry: dict, collection, retriever, n_results: int, retrieval_only: bool
) -> dict:
    """Wertet eine Frage aus und liefert eine Ergebniszeile für den Report."""
    question = entry["question"]
    row = {
        "question": question,
        "type": entry.get("type", "?"),
        "unanswerable": is_unanswerable(entry),
    }

    if retrieval_only:
        hits = retriever(collection, question, n_results=n_results)
    else:
        result = answer(question, n_results=n_results, collection=collection, retriever=retriever)
        hits = result["hits"]

    if not row["unanswerable"]:
        evidence = entry.get("evidence", [])
        expected = entry["expected_source"]
        row["source_hit"] = source_hit(expected, hits)
        # Belege zählen nur aus der erwarteten Datei, damit ein Ablenker nicht mitzählt.
        own_hits = [hit for hit in hits if hit["source"] == expected]
        row["evidence_found"] = count_evidence(evidence, own_hits)
        row["evidence_total"] = len(evidence)

    if retrieval_only:
        return row

    row["abstained"] = is_abstention(result["answer"])
    row["claims"] = None
    row["faithfulness"] = None
    row["answer_relevancy"] = None
    # Der Judge bewertet nur echte Antworten. Enthaltungen zählt der Report getrennt.
    if not row["unanswerable"] and not row["abstained"]:
        row["claims"] = judge_claims(question, result["answer"], result["context"])
        row["faithfulness"] = supported_share(row["claims"])
        row["answer_relevancy"] = answer_relevancy(question, result["answer"])
    return row


def evidence_complete(row: dict) -> bool:
    """Beleg-Treffer: Alle Belegstellen stehen in Chunks der erwarteten Datei im Kontext."""
    return row["evidence_found"] == row["evidence_total"]


# --- Report -----------------------------------------------------------------

_COLUMNS = "  {typ:<15}{frage:<46}{datei:<7}{belege:<8}"
_ANSWER_COLUMNS = "{antwort:<14}{faith:<7}{relev}"


def _short(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def _fmt(value: float | None) -> str:
    return "–" if value is None else f"{value:.2f}"


def _mean(values: list[float | None]) -> tuple[float | None, int]:
    """Mittelwert über die bewerteten Werte (None zählt nicht) und deren Anzahl."""
    rated = [value for value in values if value is not None]
    return (sum(rated) / len(rated) if rated else None), len(rated)


def _verdict(row: dict) -> str:
    """Antwortverhalten. Das Kreuz markiert das falsche Verhalten."""
    if row["unanswerable"]:
        return "Enthaltung ✓" if row["abstained"] else "Antwort ✗"
    return "Enthaltung ✗" if row["abstained"] else "Antwort"


def _print_cells(cells: dict, retrieval_only: bool) -> None:
    line = _COLUMNS.format(**cells)
    if not retrieval_only:
        line += _ANSWER_COLUMNS.format(**cells)
    print(line.rstrip())


def print_header(retrieval_only: bool) -> None:
    header = {"typ": "Typ", "frage": "Frage", "datei": "Datei", "belege": "Belege",
              "antwort": "Antwort", "faith": "Faith", "relev": "Relev"}
    _print_cells(header, retrieval_only)


def print_row(row: dict, retrieval_only: bool, details: bool = False) -> None:
    cells = {
        "typ": row["type"],
        "frage": _short(row["question"], 44),
        "datei": "–",
        "belege": "–",
        "antwort": "",
        "faith": _fmt(row.get("faithfulness")),
        "relev": _fmt(row.get("answer_relevancy")),
    }
    if not row["unanswerable"]:
        cells["datei"] = "✓" if row["source_hit"] else "✗"
        cells["belege"] = f"{row['evidence_found']}/{row['evidence_total']}"
    if not retrieval_only:
        cells["antwort"] = _verdict(row)
    _print_cells(cells, retrieval_only)

    if details and row.get("claims"):
        for claim in row["claims"]:
            mark = "✓" if claim["gestützt"] else "✗"
            print(f"      {mark} {claim.get('aussage', '?')}")


def print_report(
    rows: list[dict], retriever_name: str, n_results: int, retrieval_only: bool
) -> None:
    answerable = [row for row in rows if not row["unanswerable"]]
    unanswerable = [row for row in rows if row["unanswerable"]]
    mode = "nur Retrieval" if retrieval_only else "mit Antworten"

    print("=" * 78)
    print(f"RAG-Evaluation · retriever={retriever_name} · n={n_results} · {mode} · "
          f"{len(rows)} Fragen")
    print("=" * 78)
    if answerable:
        files = sum(row["source_hit"] for row in answerable)
        complete = sum(evidence_complete(row) for row in answerable)
        total = len(answerable)
        print(f"  Datei-Treffer:            {files}/{total} beantwortbare Fragen")
        print(f"  Beleg-Treffer:            {complete}/{total} (alle Belege im Kontext)")
        missing = [row["question"] for row in answerable if not evidence_complete(row)]
        if missing:
            print("  Ohne vollständigen Beleg:")
            for question in missing:
                print(f"    - {question}")

    if not retrieval_only:
        if unanswerable:
            correct = sum(row["abstained"] for row in unanswerable)
            print(f"  Enthaltung korrekt:       {correct}/{len(unanswerable)} "
                  "unbeantwortbare Fragen")
        if answerable:
            wrong = sum(row["abstained"] for row in answerable)
            print(f"  Fälschliche Enthaltung:   {wrong}/{len(answerable)} beantwortbare Fragen")
            answered = [row for row in answerable if not row["abstained"]]
            for metric, label in (
                ("faithfulness", "Faithfulness (Ø):"),
                ("answer_relevancy", "Answer Relevancy (Ø):"),
            ):
                mean, rated = _mean([row[metric] for row in answered])
                rated_text = f"(bewertet: {rated} von {len(answered)} Antworten)"
                print(f"  {label:<26}{_fmt(mean)}  {rated_text}")
            print("  Richtwerte: Faithfulness > 0.8 stark, < 0.5 bedenklich")
            print("              Answer Relevancy > 0.8 stark, < 0.6 bedenklich")
    print("=" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG-Evaluation auf eval/rag_eval.jsonl")
    parser.add_argument(
        "--retriever",
        choices=RETRIEVER_NAMES,
        default="dense",
        help="Retrieval-Verfahren (Default: dense)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=5,
        help="Anzahl Kontext-Chunks (Default: 5). Mit 3 werden Unterschiede sichtbar.",
    )
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="nur Retrieval messen, keine Chat-Aufrufe",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Einzelurteile des Faithfulness-Judges ausgeben",
    )
    parser.add_argument("--evalset", type=Path, default=EVAL_PATH, help="Pfad zum Evalset")
    args = parser.parse_args()

    collection = create_collection(DEFAULT_COLLECTION)
    if collection.count() == 0:
        raise SystemExit("Die Collection ist leer. Zuerst indexieren: python -m src.ingest docs")

    retriever = resolve_retriever(args.retriever)
    rows = []
    print_header(args.retrieval_only)
    for entry in load_evalset(args.evalset):
        row = evaluate_entry(entry, collection, retriever, args.n, args.retrieval_only)
        print_row(row, args.retrieval_only, details=args.details)
        rows.append(row)
    print_report(rows, args.retriever, args.n, args.retrieval_only)


if __name__ == "__main__":
    main()
