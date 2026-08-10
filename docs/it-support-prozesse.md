# IT-Support-Prozesse bei LeineTech

Stand: Mai 2026

## Kontaktwege

| Kanal | Wann | Erreichbarkeit |
|---|---|---|
| Ticketportal <https://tickets.leinetech.intern> | Standardweg für alle Anliegen | rund um die Uhr |
| E-Mail an `it-support@leinetech.de` | erzeugt automatisch ein Ticket | rund um die Uhr |
| Hotline intern **-4242** (extern +49 511 4790-4242) | dringende Fälle, Komplettausfälle, Verlust/Diebstahl | Mo–Fr 7:30–18:00, danach Rufbereitschaft |
| IT-Service-Point, Raum 1.08 | Geräteausgabe, Ausweis koppeln, persönliche Hilfe | Mo–Fr 9:00–16:00 |

## Ticket-Kategorien

Jedes Ticket wird einer von fünf Kategorien zugeordnet:

| Kategorie | Inhalt (Beispiele) |
|---|---|
| **Hardware** | Notebooks, Bildschirme, Dockingstations, Drucker(-geräte), Headsets, Defekte und Bestellungen |
| **Software** | Anwendungsfehler, Abstürze, Updates/Installationen, Lizenzen, interne Fachanwendungen (FinanzPro, TimeTrack, CRM-Connect, ContractHub, LT-Deploy) |
| **Netzwerk** | WLAN, LAN-Dosen, VPN-/Verbindungsprobleme, Internetzugang, DNS/Routing |
| **Zugang** | Passwörter, Kontosperrungen, MFA, Berechtigungen, Shared Mailboxes, On-/Offboarding von Accounts |
| **Abrechnung** | Rechnungen, Kostenstellen, Tarife/Abos, Zahlungen, Klärungen mit Anbietern und Buchhaltung |

Maßgeblich ist das **eigentliche Problem**, nicht einzelne Stichworte: Ein Absturz des
Rechnungsmoduls ist ein **Software**-Fall, eine doppelte Abbuchung ein **Abrechnung**-Fall,
und fehlender Laufwerkszugriff trotz stehendem VPN-Tunnel meist ein **Netzwerk**-Fall.

## Prioritäten und SLA-Reaktionszeiten

| Priorität | Kriterien | Reaktionszeit (SLA) |
|---|---|---|
| **hoch** | Produktionsausfall; viele Nutzer oder ein ganzes Team blockiert; kein Workaround; drohender Datenverlust; Sicherheitsvorfall | **2 Stunden** |
| **mittel** | Einzelperson eingeschränkt, Workaround vorhanden oder Arbeit teilweise möglich | **8 Stunden** |
| **niedrig** | allgemeine Fragen, Wünsche, Bestellungen ohne Termindruck, kosmetische Fehler | **3 Werktage** |

Hinweise zur Einstufung:

- Die Priorität richtet sich nach der **Auswirkung**, nicht nach der Wortwahl. Auch ein höflich formuliertes "kein Stress" kann ein Hoch-Prio-Fall sein, wenn ein Team nicht arbeiten kann.
- Reaktionszeit bedeutet: qualifizierte erste Rückmeldung durch den Service Desk, nicht garantierte Lösung.
- Bei Priorität hoch außerhalb der Servicezeiten greift die Rufbereitschaft (nur per Hotline).

## Eskalationsweg

1. **1st Level — Service Desk:** Annahme, Kategorisierung, Priorisierung, Lösung von Standardfällen.
2. **2nd Level — Fachteams:** Client-Team, Netzwerk-Team, Identity-Team, Team Fachanwendungen.
3. **3rd Level — Hersteller / Entwicklung:** Lenovo/Apple/Canon-Service, Cisco TAC, internes Entwicklungsteam.

Formale Eskalation (SLA gerissen, keine Rückmeldung): zuerst Kommentar im Ticket mit dem
Stichwort "Eskalation", danach Leitung IT-Service (**Bernd Hagedorn**, Durchwahl -4200).

## Ticket-Lebenszyklus

`Neu` → `In Bearbeitung` → ggf. `Warten auf Rückmeldung` → `Gelöst` → `Geschlossen`

- Tickets in "Warten auf Rückmeldung" werden nach **5 Werktagen** ohne Antwort automatisch geschlossen (Erinnerung nach 3 Werktagen).
- Gelöste Tickets können innerhalb von 5 Werktagen wieder geöffnet werden, danach bitte ein neues Ticket mit Verweis auf das alte.

## Was gehört in ein gutes Ticket?

- **Was** funktioniert nicht (genaue Fehlermeldung, Fehlercode, Screenshot)?
- **Seit wann**, was wurde zuletzt geändert (Update, Umzug, neues Gerät)?
- **Wer/wie viele** sind betroffen? Gibt es einen Workaround?
- Gerätenummer (`LT-NB-xxxx`, `LT-PRN-xx`) bzw. Dosen-/Raumnummer, wenn relevant.
- Termindruck explizit nennen (z. B. Kundenworkshop am Datum X).

## FAQ

**Kann ich die Priorität selbst setzen?**
Sie können eine Einschätzung angeben; verbindlich festgelegt wird die Priorität vom Service Desk anhand der Kriterien oben.

**Mein Ticket ist dringend geworden — neues Ticket?**
Nein. Kommentar ins bestehende Ticket schreiben und bei akutem Bedarf die Hotline -4242 anrufen, der Service Desk stuft dann hoch.

**Wie sehe ich den Stand meiner Tickets?**
Im Ticketportal unter "Meine Tickets"; bei jeder Statusänderung gibt es zusätzlich eine E-Mail.

**Gibt es Support am Wochenende?**
Nur Rufbereitschaft für Priorität hoch über die Hotline. Alle anderen Anliegen werden am nächsten Werktag bearbeitet.
