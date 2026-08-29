# Diese Datei ist absichtlich leer — sie muss nur EXISTIEREN.
#
# pytest nimmt das Verzeichnis mit der obersten conftest.py als rootdir und
# legt es in sys.path. Deshalb funktioniert `from src.triage import ...` in
# tests/ ohne Installation. Nicht dieser Kommentar bewirkt das, sondern die
# bloße Anwesenheit der Datei.
#
# Für VL 9 wird sie ohnehin nicht gebraucht: tools/mutation_dojo.py und
# tools/spec_gate.py setzen sys.path selbst und laufen ohne pytest.
