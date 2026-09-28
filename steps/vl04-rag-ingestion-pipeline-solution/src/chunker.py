"""Chunking: zerlegt Dokumente in Stücke, die einzeln eingebettet werden.

Warum chunken? Ein ganzer Artikel als ein einziger Vektor mischt alle seine
Themen. Der Vektor von `vpn-zugang.md` läge zwischen „VPN einrichten“,
„Split-Tunneling“ und „FAQ“ und passte zu keiner konkreten Frage gut. Kleinere
Chunks ergeben schärfere Treffer bei der semantischen Suche.

Umgesetzt ist rekursives Chunking (Strategie 2 aus der Vorlesung) in vier Schritten:

1. Rekursiv trennen: erst an Absätzen, zu große Stücke an Zeilen, im Notfall an Sätzen.
2. Packen: aufeinanderfolgende Stücke zusammenfassen, bis `chunk_size` erreicht ist.
3. Verschmelzen: sehr kurze Chunks an ihren Nachbarn hängen.
4. Überlappen: jedem Chunk das Ende seines Vorgängers voranstellen. Ein Satz, der
   auf der Grenze liegt, steht dann vollständig im Folge-Chunk.

Alle Längen zählen Zeichen, nicht Tokens.
"""

import re

# Reihenfolge = Priorität: erst Absätze, dann Zeilen, zuletzt Sätze.
_SEPARATORS = ["\n\n", "\n", ". "]


def chunk_document(
    document: dict,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict]:
    """Zerlegt ein Dokument in Chunks.

    Jeder Chunk erbt die Metadaten des Dokuments und bekommt eine eindeutige
    `chunk_id` der Form `<source>::<laufende Nummer>`, z. B. `vpn-zugang.md::4`.

    Args:
        document: Dict mit "text" und "metadata" (Format von loader.load_documents).
        chunk_size: Obergrenze in Zeichen für die gepackten Stücke. Die vorangestellte
            Überlappung kann einen Chunk um bis zu chunk_overlap + 1 Zeichen verlängern.
        chunk_overlap: höchstens so viele Zeichen vom Ende des Vorgängers werden
            jedem Chunk vorangestellt. Kürzere Chunks werden verschmolzen.

    Returns:
        Liste von Dicts {"text", "metadata", "chunk_id"} in Dokumentreihenfolge.
    """
    metadata = document.get("metadata", {})
    source = metadata.get("source", "unbekannt")

    pieces = _recursive_split(document["text"], chunk_size, _SEPARATORS)
    packed = _pack(pieces, chunk_size)
    merged = _merge_small(packed, chunk_overlap)
    overlapped = _add_overlap(merged, chunk_overlap)

    return [
        {
            "text": text,
            "metadata": dict(metadata),  # eigene Kopie, damit sich Chunks nichts teilen
            "chunk_id": f"{source}::{number}",
        }
        for number, text in enumerate(overlapped)
    ]


def _recursive_split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    """Zerlegt Text rekursiv in Stücke von höchstens chunk_size Zeichen.

    Probiert die Trennzeichen der Reihe nach. Ein Stück, das schon passt, bleibt
    ganz. Ist kein Trennzeichen mehr übrig, wird als letzter Ausweg hart nach
    chunk_size geschnitten (Strategie 1).
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return [text[start:start + chunk_size] for start in range(0, len(text), chunk_size)]

    separator, *finer_separators = separators
    if separator not in text:
        return _recursive_split(text, chunk_size, finer_separators)

    parts = text.split(separator)
    # Das Trennzeichen bleibt am Teil. Bei ". " bleibt so der Satzpunkt erhalten.
    parts = [part + separator for part in parts[:-1]] + parts[-1:]

    pieces = []
    for part in parts:
        pieces.extend(_recursive_split(part, chunk_size, finer_separators))
    return pieces


def _pack(pieces: list[str], chunk_size: int) -> list[str]:
    """Fasst aufeinanderfolgende Stücke gierig zusammen, solange chunk_size reicht.

    Verbunden wird mit einem Zeilenumbruch. So bleiben Überschriften und
    Listenpunkte auf eigenen Zeilen wie im Markdown-Original.
    """
    chunks: list[str] = []
    buffer = ""
    for piece in pieces:
        if not buffer:
            buffer = piece
        elif len(buffer) + 1 + len(piece) <= chunk_size:
            buffer = f"{buffer}\n{piece}"
        else:
            chunks.append(buffer)
            buffer = piece
    if buffer:
        chunks.append(buffer)
    return chunks


def _merge_small(chunks: list[str], min_size: int) -> list[str]:
    """Hängt Chunks, die kürzer als min_size sind, an ihren Nachfolger.

    Ein sehr kurzer Chunk (z. B. eine einzelne Überschrift) trägt allein kaum
    Bedeutung. Bleibt ganz am Ende ein kurzer Rest übrig, wandert er an den
    Vorgänger.
    """
    if min_size <= 0:
        return chunks

    result: list[str] = []
    index = 0
    while index < len(chunks):
        current = chunks[index]
        while len(current) < min_size and index + 1 < len(chunks):
            index += 1
            current = f"{current}\n{chunks[index]}"
        if len(current) < min_size and result:
            result[-1] = f"{result[-1]}\n{current}"
        else:
            result.append(current)
        index += 1
    return result


def _add_overlap(chunks: list[str], chunk_overlap: int) -> list[str]:
    """Stellt jedem Chunk außer dem ersten das Ende seines Vorgängers voran."""
    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for previous, current in zip(chunks, chunks[1:]):
        tail = _tail_at_word_boundary(previous, chunk_overlap)
        overlapped.append(f"{tail}\n{current}" if tail else current)
    return overlapped


def _tail_at_word_boundary(text: str, max_chars: int) -> str:
    """Liefert höchstens max_chars Zeichen vom Textende, beginnend an einer Wortgrenze.

    Ohne diese Korrektur begänne die Überlappung oft mitten im Wort („nternet“).
    Ist der Text höchstens max_chars lang, wird er ganz übernommen. Ohne diesen
    Fall gäbe es unten beim Zugriff auf text[-max_chars - 1] einen IndexError.
    Enthält das Ende gar keinen Leerraum, wird es ungekürzt übernommen.
    """
    if len(text) <= max_chars:
        return text.strip()
    tail = text[-max_chars:]
    if not text[-max_chars - 1].isspace():
        # Der Schnitt liegt mitten in einem Wort: erst nach dem nächsten Leerraum beginnen.
        match = re.search(r"\s", tail)
        if match:
            tail = tail[match.end():]
    return tail.strip()
