"""RAG-Evaluation per LLM-as-Judge — die RAG-Triade auf einem kleinen Evalset.

RAG kann an zwei Stellen scheitern (Retrieval ODER Generierung), und eine
falsche Antwort sieht von aussen immer gleich aus. Deshalb messen wir drei
komplementaere Signale — die **RAG-Triade**:

    Kontext-Treffer   War die erwartete Quelle unter den Chunks?   (RETRIEVAL)
    Faithfulness      Ist jede Aussage durch den Kontext gedeckt?  (GROUNDING)
    Answer Relevancy  Beantwortet die Antwort die Frage?           (GENERIERUNG)

Das ist das Verfahren hinter RAGAS: **LLM-as-Judge**. Wir bewerten ein LLM mit
einem LLM — die Zahlen sind **Richtungssignale zum Vergleich von
Konfigurationen**, keine absolute Wahrheit (Positions-/Ausfuehrlichkeits-/
Selbstverstaerkungsbias). Fuer die echte Produktion nimmt man das `ragas`-Paket
(siehe README); hier bleiben wir bewusst abhaengigkeitsfrei auf dem Kurs-Endpunkt.

Unbeantwortbare Fragen zaehlen als korrekt, wenn das System sich **enthaelt**
(Abstinenz) statt zu halluzinieren.

Aufruf:
    python -m src.rag_eval                    # Baseline: dense
    python -m src.rag_eval --retriever hybrid
    python -m src.rag_eval --retriever hybrid --n 3   # kleineres k: Unterschiede sichtbar
"""

import argparse
import json
import re
from pathlib import Path

from src.llm import chat
from src.rag import answer
from src.search import embedding_search
from src.vectorstore import DEFAULT_COLLECTION, create_collection

EVAL_PATH = Path("eval/rag_eval.jsonl")
UNANSWERABLE = "nicht in der wissensbasis"


def load_evalset(path: Path = EVAL_PATH) -> list[dict]:
    """Laedt das Evalset (eine JSON-Zeile pro Frage)."""
    entries = []
    with open(path, encoding="utf-8") as file:
        for line in file:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def _judge_score(prompt: str) -> float:
    """Fragt den LLM-Richter und parst eine Dezimalzahl in [0, 1] aus der Antwort."""
    raw = chat(
        prompt,
        system="Du bist ein strenger, praeziser Bewerter. "
        "Antworte AUSSCHLIESSLICH mit einer Dezimalzahl zwischen 0 und 1.",
        temperature=0.0,
    )
    match = re.search(r"\d+(?:[.,]\d+)?", raw)
    if not match:
        return 0.0
    value = float(match.group().replace(",", "."))
    return max(0.0, min(1.0, value))


def faithfulness(question: str, rag_answer: str, context: str) -> float:
    """Anteil der Antwort-Aussagen, die durch den Kontext gestuetzt sind.

    ``question`` ist Teil der Signatur (wie im Lab vorgegeben), damit der Judge
    Aussagen im Kontext der Frage bewerten kann; das Grounding-Urteil selbst
    stuetzt sich aber vor allem auf KONTEXT vs. ANTWORT.
    """
    return _judge_score(
        f"FRAGE:\n{question}\n\n"
        f"KONTEXT:\n{context}\n\n"
        f"ANTWORT:\n{rag_answer}\n\n"
        "Zerlege die ANTWORT in einzelne Aussagen. Welcher Anteil davon wird "
        "durch den KONTEXT gestuetzt? Gib das Verhaeltnis gestuetzt/gesamt als "
        "Dezimalzahl zwischen 0 und 1 zurueck. Nur die Zahl."
    )


def answer_relevancy(question: str, rag_answer: str) -> float:
    """Wie direkt beantwortet die Antwort die Frage (0 = gar nicht, 1 = perfekt)?"""
    return _judge_score(
        f"FRAGE:\n{question}\n\n"
        f"ANTWORT:\n{rag_answer}\n\n"
        "Wie direkt und vollstaendig beantwortet die ANTWORT die FRAGE? "
        "Wenn man aus der Antwort die urspruengliche Frage rekonstruieren kann, "
        "ist die Relevanz hoch. Gib eine Dezimalzahl zwischen 0 und 1 zurueck. "
        "Nur die Zahl."
    )


def is_abstention(rag_answer: str) -> bool:
    """Hat sich das System enthalten (statt zu halluzinieren)?"""
    text = rag_answer.lower()
    return UNANSWERABLE in text or "keine information" in text


def context_hit(expected_source: str, hits: list[dict]) -> bool:
    """War die erwartete Quelle unter den abgerufenen Chunks?"""
    return any(hit["source"] == expected_source for hit in hits)


def _resolve_retriever(name: str):
    """CLI-Wahl (String) → Retriever-Funktion für answer()."""
    if name == "hybrid":
        from src.hybrid import hybrid_search

        return hybrid_search
    return embedding_search


def evaluate(retriever: str = "dense", n_results: int = 5) -> list[dict]:
    """Beantwortet jede Eval-Frage und bewertet sie per LLM-as-Judge."""
    collection = create_collection(DEFAULT_COLLECTION)
    if collection.count() == 0:
        raise SystemExit(
            "Collection ist leer — zuerst die Pipeline laufen lassen: "
            "python -m src.ingest docs"
        )

    retriever_fn = _resolve_retriever(retriever)

    rows = []
    for entry in load_evalset():
        question = entry["question"]
        result = answer(
            question,
            n_results=n_results,
            collection=collection,
            retriever=retriever_fn,
        )
        rag_answer = result["answer"]
        row = {"question": question, "type": entry.get("type", "?")}

        if entry.get("ground_truth", "").strip().lower() == UNANSWERABLE:
            # Unbeantwortbar: korrekt = das System hat sich enthalten.
            # Konvention (siehe Lab): Faithfulness/Relevancy = 1.0 bei korrekter
            # Enthaltung, 0.0 bei Halluzination — so fließen diese Fragen in
            # dieselben Mittelwerte ein wie die beantwortbaren.
            abstained = is_abstention(rag_answer)
            row["abstained"] = abstained
            row["faithfulness"] = 1.0 if abstained else 0.0
            row["answer_relevancy"] = 1.0 if abstained else 0.0
        else:
            row["context_hit"] = context_hit(
                entry.get("expected_source", ""), result["hits"]
            )
            row["faithfulness"] = faithfulness(question, rag_answer, result["context"])
            row["answer_relevancy"] = answer_relevancy(question, rag_answer)

        rows.append(row)
        _print_row(row)
    return rows


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _print_row(row: dict) -> None:
    if "context_hit" in row:
        print(
            f"  {row['question'][:52]:52} "
            f"faith={row['faithfulness']:.2f}  "
            f"relev={row['answer_relevancy']:.2f}  "
            f"ctx={'✓' if row['context_hit'] else '✗'}"
        )
    else:
        print(
            f"  {row['question'][:52]:52} "
            f"Enthaltung={'✓' if row['abstained'] else '✗ (halluziniert!)'}"
        )


def print_report(rows: list[dict], retriever: str) -> None:
    answerable = [r for r in rows if "context_hit" in r]
    unanswerable = [r for r in rows if "abstained" in r]

    config = f"retriever={retriever}"
    print("\n" + "=" * 64)
    print(f"RAG-EVALUATION ({config}) — {len(rows)} Fragen")
    print("=" * 64)
    # Faithfulness/Relevancy über ALLE Fragen (unbeantwortbare zählen mit 1.0/0.0).
    print(f"  Faithfulness (Ø):     {_mean([r['faithfulness'] for r in rows]):.2f}")
    print(f"  Answer Relevancy (Ø): {_mean([r['answer_relevancy'] for r in rows]):.2f}")
    print(
        f"  Kontext-Treffer:      "
        f"{sum(r['context_hit'] for r in answerable)}/{len(answerable)}"
    )
    if unanswerable:
        print(
            f"  Enthaltung korrekt:   "
            f"{sum(r['abstained'] for r in unanswerable)}/{len(unanswerable)}"
        )
    print("=" * 64)
    print(
        "  Richtwerte: Faithfulness >0.8 stark, <0.5 bedenklich · "
        "Relevancy >0.8 stark, <0.6 bedenklich"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG-Evaluation per LLM-as-Judge")
    parser.add_argument(
        "--retriever",
        choices=["dense", "hybrid"],
        default="dense",
        help="Retrieval-Verfahren (Default: dense)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=5,
        help="Anzahl Kontext-Chunks (Default: 5). Kleineres k (z. B. 3) macht "
        "Retrieval-Unterschiede zwischen dense und hybrid sichtbar.",
    )
    args = parser.parse_args()

    rows = evaluate(retriever=args.retriever, n_results=args.n)
    print_report(rows, args.retriever)


if __name__ == "__main__":
    main()
