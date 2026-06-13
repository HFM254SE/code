# E-Mail und Kalender (Outlook / Exchange Online)

Stand: Mai 2026

LeineTech nutzt **Exchange Online** (Microsoft 365) mit Outlook als Standard-Client.
Die Anmeldung läuft über das zentrale Konto mit MFA; VPN ist für E-Mail **nicht** erforderlich.

## Postfachgröße und Archiv

- Jedes Postfach hat **10 GB** Speicher.
- Ab **9 GB** erscheint eine Warnung, ab **9,5 GB** ist kein Versand mehr möglich (Empfang funktioniert weiter).
- Das **Online-Archiv** (zusätzlich 50 GB) ist für alle aktiviert: Elemente älter als 18 Monate werden automatisch verschoben.
- Anhänge sind auf **25 MB** begrenzt — größere Dateien bitte über OneDrive/SharePoint-Link teilen.

## Bekannte Fehler beim Senden

### Fehlermeldung 0x80042109 ("Server nicht erreichbar") beim Senden
Tritt erfahrungsgemäß nach Office-Updates auf, wenn das Outlook-Sendeprofil beschädigt wurde:
1. Outlook beenden.
2. Systemsteuerung → "Mail (Microsoft Outlook)" → Profile anzeigen → "Hinzufügen" und ein neues Profil anlegen.
3. Das neue Profil als Standard setzen und Outlook starten — das Konto richtet sich automatisch ein.
4. Hängengebliebene Mails aus dem alten Postausgang erneut senden.

Hilft das nicht, Ticket mit Kategorie **Software** und genauem Fehlercode eröffnen.

### Mails bleiben im Postausgang
- Prüfen, ob der Anhang über 25 MB liegt.
- Offline-Modus prüfen: Menüband → Senden/Empfangen → "Offline arbeiten" darf nicht aktiv sein.

## Shared Mailboxes (Funktionspostfächer)

- Funktionspostfächer (z. B. `vertrieb@leinetech.de`, `it-support@leinetech.de`) werden per Ticket beantragt, Kategorie **Zugang**.
- Erforderlich: Name des Postfachs, Zweck, verantwortliche Person, Liste der Mitglieder, Freigabe der Teamleitung.
- Mitglieder erhalten das Postfach in Outlook automatisch innerhalb von 24 Stunden nach Freischaltung.
- Versand "im Auftrag von" oder "als" das Postfach bitte im Ticket explizit angeben.

## Kalenderfreigabe

1. Outlook → Kalender → Rechtsklick auf den eigenen Kalender → "Freigeben".
2. Empfänger und Detailgrad wählen: *Verfügbarkeit*, *Eingeschränkte Details* oder *Alle Details*.
3. Firmenweit ist standardmäßig die **Verfügbarkeit** (Frei/Gebucht) für alle sichtbar.
4. Stellvertretungen (z. B. Assistenz bucht Termine): Datei → Kontoeinstellungen → "Zugriffsrechte für Stellvertretung".

## Raumbuchung

Besprechungsräume (u. a. *Leine*, *Ihme*, *Maschsee*) werden als Teilnehmer in die Termineinladung
aufgenommen und bestätigen automatisch. Räume mit Videokonferenztechnik sind im Raumnamen mit
"[VC]" gekennzeichnet.

## Abwesenheitsnotiz und Weiterleitung

- Abwesenheitsnotiz: Datei → "Automatische Antworten" (bitte mit Vertretung und Rückkehrdatum).
- Automatische Weiterleitung an **externe** Adressen ist aus Sicherheitsgründen technisch gesperrt.

## FAQ

**Mein Postfach ist voll — bekomme ich mehr Speicher?**
Nein, 10 GB sind die feste Obergrenze. Altes in das Online-Archiv verschieben (Rechtsklick → Verschieben → Archiv) oder große Anhänge löschen.

**Kann ich mein privates Handy anbinden?**
Ja, über Outlook Mobile mit Intune-Registrierung. Native Mail-Apps werden nicht unterstützt.

**Wie bekomme ich Zugriff auf den Kalender eines Kollegen?**
Der Kollege muss den Kalender selbst freigeben (siehe oben); die IT richtet keine Freigaben ohne Zustimmung ein.

**Werden gelöschte Mails gesichert?**
Gelöschte Elemente sind 30 Tage wiederherstellbar (Ordner "Gelöschte Elemente" → "Vom Server wiederherstellen"). Danach hilft nur ein Ticket; Wiederherstellung ist bis 90 Tage möglich.
