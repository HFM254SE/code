def print_stats(results, extra=[]):
    h = 0
    s = 0
    n = 0
    z = 0
    a = 0
    for r in results:
        if r["kategorie"] == "Hardware":
            h = h + 1
    for r in results:
        if r["kategorie"] == "Software":
            s = s + 1
    for r in results:
        if r["kategorie"] == "Netzwerk":
            n = n + 1
    for r in results:
        if r["kategorie"] == "Zugang":
            z = z + 1
    for r in results:
        if r["kategorie"] == "Abrechnung":
            a = a + 1
    hoch = 0
    mittel = 0
    niedrig = 0
    for r in results:
        if r["prioritaet"] == "hoch":
            hoch = hoch + 1
    for r in results:
        if r["prioritaet"] == "mittel":
            mittel = mittel + 1
    for r in results:
        if r["prioritaet"] == "niedrig":
            niedrig = niedrig + 1
    print("=" * 60)
    print("TICKET-STATISTIK LEINETECH SUPPORT")
    print("=" * 60)
    print("Hardware: " + str(h) + "  Software: " + str(s) + "  Netzwerk: " + str(n) + "  Zugang: " + str(z) + "  Abrechnung: " + str(a))
    print("Prioritaeten: hoch=" + str(hoch) + " mittel=" + str(mittel) + " niedrig=" + str(niedrig))
    print("=" * 60)
