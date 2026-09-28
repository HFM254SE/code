"""Chunking: zerlegt Dokumente in einzeln eingebettete Stücke (Lab VL 4, Teil 1B).

Umgesetzt wird rekursives Chunking (Strategie 2 aus der Vorlesung) in vier Schritten:

1. Rekursiv trennen: erst an Absätzen, zu große Stücke an Zeilen, im Notfall an Sätzen.
   → TODO Teil 1B-1 in `_recursive_split`
2. Packen: aufeinanderfolgende Stücke zusammenfassen, bis `chunk_size` erreicht ist.
   → fertig in `_pack`
3. Verschmelzen: sehr kurze Chunks an ihren Nachbarn hängen.
   → fertig in `_merge_small`
4. Überlappen: jedem Chunk das Ende seines Vorgängers voranstellen.
   → TODO Teil 1B-2 in `_add_overlap`

Zum Schluss bekommt jeder Chunk Metadaten und eine chunk_id (TODO Teil 1B-3).
Alle Längen zählen Zeichen, nicht Tokens.

Prüfen:
    python -m pytest tests/test_chunker.py -q
"""

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
        chunk_size: Obergrenze in Zeichen für die gepackten Stücke.
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

    # TODO Teil 1B-3: Für jeden Text in `overlapped` ein Dict bauen und als Liste zurückgeben:
    #   {"text": text, "metadata": dict(metadata), "chunk_id": f"{source}::{nummer}"}
    #   Die Nummer zählt ab 0 (enumerate). dict(metadata) gibt jedem Chunk eine eigene Kopie.
    raise NotImplementedError("TODO Teil 1B-3: Chunk-Dicts in chunk_document (src/chunker.py)")


def _recursive_split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    """Zerlegt Text rekursiv in Stücke von höchstens chunk_size Zeichen.

    Probiert die Trennzeichen der Reihe nach. Ein Stück, das schon passt, bleibt
    ganz. Ist kein Trennzeichen mehr übrig, wird als letzter Ausweg hart nach
    chunk_size geschnitten (Strategie 1).
    """
    # TODO Teil 1B-1:
    #   1. text.strip(). Leerer Text ergibt [].
    #   2. Passt der Text (len <= chunk_size): [text] zurückgeben.
    #   3. Keine Trennzeichen mehr übrig: hart in Stücke zu chunk_size Zeichen schneiden.
    #   4. Sonst das erste Trennzeichen nehmen (separator, *feiner = separators).
    #      Kommt es im Text nicht vor: mit den feineren Trennzeichen weitermachen.
    #   5. Am Trennzeichen splitten. Wichtig: Das Trennzeichen am Ende jedes Teils
    #      (außer dem letzten) wieder anhängen, sonst gehen bei ". " die Satzpunkte verloren.
    #   6. Jeden Teil rekursiv mit den feineren Trennzeichen zerlegen und alle Stücke sammeln.
    raise NotImplementedError("TODO Teil 1B-1: _recursive_split in src/chunker.py")


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
    # TODO Teil 1B-2:
    #   1. Bei chunk_overlap <= 0 oder höchstens einem Chunk: chunks unverändert zurückgeben.
    #   2. Der erste Chunk bleibt, wie er ist.
    #   3. Für jedes Nachbarpaar aus zip(chunks, chunks[1:]) den tail bestimmen:
    #      a) Ist previous höchstens chunk_overlap Zeichen lang, wird previous ganz als
    #         tail übernommen. Ohne diesen Fall gibt es in b) einen IndexError.
    #      b) Sonst tail = previous[-chunk_overlap:]. Beginnt tail mitten in einem Wort
    #         (das Zeichen davor, previous[-chunk_overlap - 1], ist kein Leerraum), tail
    #         erst nach dem ersten Leerraum beginnen lassen. Findet sich keiner, bleibt
    #         tail ganz.
    #      c) Danach tail.strip().
    #   4. Neuer Chunk: f"{tail}\n{current}". Ist tail leer, bleibt current unverändert.
    raise NotImplementedError("TODO Teil 1B-2: _add_overlap in src/chunker.py")
