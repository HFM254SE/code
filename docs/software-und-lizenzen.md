# Software und Lizenzen

Stand: Mai 2026

Software wird bei LeineTech grundsätzlich über den **Softwarekatalog im Self-Service-Portal**
(<https://portal.leinetech.intern>) installiert. Manuelle Downloads aus dem Internet sind auf
Firmengeräten technisch blockiert (Application Control).

## Softwarekatalog: drei Stufen

| Stufe | Beispiele | Genehmigung |
|---|---|---|
| Standard (frei) | 7-Zip, VS Code, Firefox, Notepad++, Bitwarden | keine — Installation sofort |
| Kostenpflichtig | IntelliJ Ultimate, Adobe Creative Cloud, Camtasia | Teamleitung (im Portal) |
| Nicht gelistet | alles andere | Teamleitung + Sicherheitsprüfung durch die IT |

## Kostenpflichtige Lizenz beantragen

1. Im Self-Service-Portal die Software suchen und "Anfordern" klicken.
2. Kostenstelle und kurze Begründung angeben.
3. Die Teamleitung erhält automatisch eine Genehmigungsaufgabe; nach Freigabe wird die Lizenz zugewiesen und die Installation freigeschaltet.
4. Status jederzeit im Portal unter "Meine Anträge" einsehbar.

> **Hinweis:** Bleibt ein Antrag länger als **3 Werktage** im Status "In Genehmigung", verschickt
> das Portal automatisch eine Erinnerung an die Teamleitung. Hängt er danach immer noch, bitte
> ein Ticket eröffnen (Kategorie **Software**) — der Service Desk kann die Genehmigung umleiten,
> z. B. bei Urlaub der Führungskraft.

## Lizenzverlängerung und Ablauf

- Jahreslizenzen (IntelliJ, Adobe) werden **zentral** verlängert; normalerweise merkt man davon nichts.
- Läuft eine Lizenz trotzdem ab (IDE im eingeschränkten Modus, Wasserzeichen o. Ä.), bitte sofort ein Ticket eröffnen — die Neuzuweisung dauert in der Regel unter einem Tag.
- Ungenutzte Lizenzen werden nach 90 Tagen ohne Nutzung automatisch entzogen (Kostenoptimierung); eine erneute Anforderung ist jederzeit möglich.

## Nicht gelistete Software

Für Software außerhalb des Katalogs gilt der Prüfprozess:
1. Ticket mit Herstellername, Produkt, Version, Link und Begründung eröffnen.
2. Die IT prüft Sicherheit (Schwachstellen, Herkunft) und Datenschutz (AVV nötig?).
3. Prüfdauer: in der Regel 5–10 Werktage. Nach Freigabe erscheint die Software im Katalog.

**Open-Source-Bibliotheken** für Entwicklungsprojekte fallen nicht unter diesen Prozess —
hier gelten die Vorgaben aus dem Entwicklungshandbuch (Dependency-Scanning in der CI).

## Interne Fachanwendungen

Folgende Anwendungen werden von LeineTech selbst betrieben und vom Team **Fachanwendungen** betreut:

| Anwendung | Zweck |
|---|---|
| FinanzPro | Finanzbuchhaltung, Fakturierung (inkl. Rechnungsmodul) |
| TimeTrack | Zeiterfassung |
| CRM-Connect | Kundenverwaltung / Vertrieb |
| ContractHub | Vertragsverwaltung |
| LT-Deploy | internes Deployment-Tool der Entwicklung |

Fehler in diesen Anwendungen (Abstürze, falsche Anzeigen, fehlgeschlagene Updates) bitte als
Ticket mit Kategorie **Software** melden — der Service Desk leitet an das Team Fachanwendungen
weiter. Bei Komplettausfällen, die ganze Teams oder die Fakturierung blockieren, gilt
Priorität **hoch** (siehe Artikel *IT-Support-Prozesse*).

## FAQ

**Darf ich privat gekaufte Software installieren?**
Nein. Auch mit privater Lizenz gilt der Katalog- bzw. Prüfprozess.

**Was passiert mit meinen Lizenzen, wenn ich das Team wechsle?**
Lizenzen wandern mit, die Kostenstelle wird beim nächsten Abrechnungslauf automatisch angepasst.

**Eine Installation aus dem Katalog schlägt fehl — was tun?**
Gerät neu starten und erneut versuchen. Bei wiederholtem Fehler Ticket mit dem genauen Fehlercode (z. B. MSI-Code 1603) eröffnen.

**Wer bezahlt die Lizenzen?**
Die Kostenstelle des anfordernden Teams. Fragen zur Zuordnung beantwortet das Controlling über ein Ticket mit Kategorie **Abrechnung**.
