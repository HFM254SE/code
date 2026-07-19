# Drucken bei LeineTech (Follow-Me-Printing)

Stand: Mai 2026

An allen Standorten gilt **Follow-Me-Printing** über PaperCut: Druckjobs werden an eine
zentrale Warteliste geschickt und erst am Gerät nach Anmeldung mit dem **Mitarbeiterausweis**
ausgegeben. Es gibt pro Etage einen Multifunktionsdrucker (Canon imageRUNNER).

## Geräteübersicht

| Gerät | Standort | Funktionen |
|---|---|---|
| LT-PRN-01 | 1. OG, neben Teeküche | Druck, Scan, Kopie |
| LT-PRN-02 | 2. OG, Flur Süd | Druck, Scan, Kopie, A3 |
| LT-PRN-03 | 3. OG, neben Besprechungsraum Leine | Druck, Scan, Kopie |
| LT-PRN-EG | Erdgeschoss, Empfang | Druck, Gästedruck |

## Einrichtung am Arbeitsplatz

1. Windows: Die Druckwarteliste `\\print.leinetech.intern\LT-FollowMe` wird über Intune automatisch eingerichtet — es ist **keine manuelle Treiberinstallation** nötig.
2. macOS: Im Self-Service-Portal (<https://portal.leinetech.intern>) das Paket "LT-FollowMe Drucker" installieren.
3. Drucken wie gewohnt auf "LT-FollowMe"; der Job bleibt bis zu **24 Stunden** in der Warteliste.
4. Am beliebigen Etagendrucker den Ausweis ans Lesefeld halten und den Job freigeben.

## Häufige Störungen und Lösungen

### Job erscheint nicht am Gerät
1. Prüfen, ob wirklich auf "LT-FollowMe" gedruckt wurde (nicht auf einen alten Direktdrucker).
2. Jobs älter als 24 Stunden werden automatisch gelöscht — erneut drucken.
3. Ausweis am Lesefeld nicht erkannt? Ausweis am IT-Service-Point (Raum 1.08) neu koppeln lassen.

### Papierstau wird gemeldet, aber kein Stau sichtbar
Der Papierweg hat mehrere Sensoren; kleine Schnipsel reichen für eine Dauermeldung:
1. Alle Fächer und beide Seitenklappen einmal vollständig öffnen und wieder schließen.
2. Gerät am Hauptschalter aus- und nach 30 Sekunden wieder einschalten.
3. Bleibt die Meldung, ein Ticket mit Gerätenummer (z. B. LT-PRN-02) eröffnen — der
   Sensor muss dann vom Technikdienstleister gereinigt/getauscht werden. Die Jobs in der
   Warteliste bleiben erhalten und können an jedem anderen Etagendrucker ausgegeben werden.

### Ausdruck hat Streifen oder blasse Stellen
Über das Bedienfeld → Wartung → "Reinigung Fixiereinheit" starten. Bei Tonermeldungen:
Toner lagert im Schrank neben dem jeweiligen Gerät; leere Kartuschen bitte in die Sammelbox.

### Scannen an E-Mail funktioniert nicht
Scan-to-Mail sendet an die eigene Firmenadresse (Voreinstellung). Andere Empfänger sind aus
Datenschutzgründen gesperrt — Dokument zuerst an sich selbst senden und dann weiterleiten.

## Gästedruck

Gäste können am Empfang (LT-PRN-EG) über den Gastzugang drucken. Dokument an
`gastdruck@leinetech.de` senden; der Empfang gibt den Job frei.

## FAQ

**Kann ich von zuhause drucken?**
Ja, mit aktiver VPN-Verbindung landet der Job in der Warteliste und kann bis zu 24 Stunden später im Büro abgeholt werden.

**Wie drucke ich A3 oder in Farbe?**
A3 kann nur LT-PRN-02 (2. OG). Farbe können alle Geräte; Standard ist aus Kostengründen Schwarz-Weiß-Duplex — Farbe im Druckdialog explizit wählen.

**Was kostet das Drucken meinem Team?**
Druckkosten werden monatlich automatisch auf die Kostenstelle des Teams umgelegt; eine Übersicht gibt es im PaperCut-Dashboard.

**Wer behebt Hardware-Defekte an den Druckern?**
Wartungsverträge laufen über den Hersteller. Bitte trotzdem immer zuerst ein Ticket eröffnen (Kategorie **Hardware**), die IT beauftragt dann den Techniker.
