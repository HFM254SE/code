"""Chunking — zerlegt Dokumente in embedding-taugliche Häppchen.

Warum überhaupt chunken? Ein Embedding-Modell hat ein festes Kontextfenster,
und ein ganzer Artikel als *ein* Vektor verwässert die Bedeutung ("VPN" und
"Drucker" landen im selben Punkt). Kleinere Chunks → schärfere Treffer bei der
späteren semantischen Suche.

Umgesetzt ist **rekursives Chunking** (Strategie 2 aus der Vorlesung): Erst an
Absätzen (`\\n\\n`) trennen, zu große Stücke an Zeilen (`\\n`), im Notfall an
Sätzen (`. `). Danach werden die Stücke gierig bis `chunk_size` zusammengepackt,
zu kleine Chunks verschmolzen und eine Überlappung eingefügt, damit ein an der
Chunk-Grenze zerschnittener Zusammenhang nicht verloren geht.
"""

# Reihenfolge = Priorität: erst Absätze, dann Zeilen, zuletzt Sätze.
_SEPARATORS = ["\n\n", "\n", ". "]


def chunk_document(
    document: dict,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict]:
    """Zerlegt ein Dokument in Chunks.

    Jeder Chunk erbt die Metadaten des Quelldokuments und bekommt eine
    eindeutige `chunk_id` (`<source>::<laufende-nummer>`).

    Args:
        document: Dict mit "text" und "metadata" (vgl. loader.load_documents).
        chunk_size: Ziel-Obergrenze für die Chunk-Länge (in Zeichen).
        chunk_overlap: Zeichen, die sich zwei aufeinanderfolgende Chunks teilen.

    Returns:
        Liste von Dicts {"text", "metadata", "chunk_id"}.
    """
    text = document["text"]
    metadata = document.get("metadata", {})
    source = metadata.get("source", "unbekannt")

    pieces = _recursive_split(text, chunk_size, _SEPARATORS)
    packed = _pack(pieces, chunk_size)
    merged = _merge_small(packed, chunk_overlap)
    overlapped = _add_overlap(merged, chunk_overlap)

    chunks = []
    for index, chunk_text in enumerate(overlapped):
        chunks.append(
            {
                "text": chunk_text,
                "metadata": dict(metadata),  # Kopie: Chunks teilen sich nichts
                "chunk_id": f"{source}::{index}",
            }
        )
    return chunks


def _recursive_split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    """Zerlegt Text rekursiv, bis jedes Stück <= chunk_size ist.

    Probiert die Separatoren der Reihe nach durch. Passt der Text schon, bleibt
    er ganz; ist kein Separator mehr übrig, wird hart nach chunk_size geschnitten.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        # Kein Trennzeichen mehr — als letzter Ausweg hart schneiden.
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator, *rest = separators
    if separator not in text:
        return _recursive_split(text, chunk_size, rest)

    pieces = []
    for part in text.split(separator):
        part = part.strip()
        if not part:
            continue
        if len(part) <= chunk_size:
            pieces.append(part)
        else:
            pieces.extend(_recursive_split(part, chunk_size, rest))
    return pieces


def _pack(pieces: list[str], chunk_size: int) -> list[str]:
    """Packt aufeinanderfolgende Stücke gierig zusammen, bis chunk_size erreicht ist."""
    chunks: list[str] = []
    buffer = ""
    for piece in pieces:
        if not buffer:
            buffer = piece
        elif len(buffer) + 1 + len(piece) <= chunk_size:
            buffer = f"{buffer} {piece}"
        else:
            chunks.append(buffer)
            buffer = piece
    if buffer:
        chunks.append(buffer)
    return chunks


def _merge_small(chunks: list[str], min_size: int) -> list[str]:
    """Verschmilzt Chunks, die kleiner als min_size sind, mit dem nächsten Chunk.

    Bleibt ganz am Ende ein Zwerg übrig (kein "nächster" mehr da), wird er an
    den vorherigen Chunk angehängt.
    """
    if min_size <= 0:
        return chunks

    result: list[str] = []
    index = 0
    while index < len(chunks):
        current = chunks[index]
        while len(current) < min_size and index + 1 < len(chunks):
            index += 1
            current = f"{current} {chunks[index]}"
        if len(current) < min_size and result:
            result[-1] = f"{result[-1]} {current}"
        else:
            result.append(current)
        index += 1
    return result


def _add_overlap(chunks: list[str], chunk_overlap: int) -> list[str]:
    """Stellt jedem Chunk (außer dem ersten) das Ende des Vorgängers voran."""
    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for previous, current in zip(chunks, chunks[1:]):
        tail = previous[-chunk_overlap:]
        overlapped.append(f"{tail} {current}")
    return overlapped
