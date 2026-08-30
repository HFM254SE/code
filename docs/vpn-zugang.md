# VPN-Zugang (Cisco AnyConnect)

Stand: Mai 2026

Der Fernzugriff auf das LeineTech-Netz erfolgt ausschließlich über **Cisco Secure Client (AnyConnect)**.
Das VPN-Gateway lautet `vpn.leinetech.de`. Die Anmeldung erfordert das persönliche Konto plus
**MFA** über die Microsoft-Authenticator-App (siehe Artikel *Passwort und Konto*).

## Voraussetzungen

- Verwaltetes Firmengerät (ThinkPad oder MacBook aus dem Standardkatalog)
- Cisco Secure Client ab Version 5.1 (wird über Intune automatisch verteilt)
- Eingerichtete MFA (Microsoft Authenticator)
- Internetanschluss mit mindestens 16 Mbit/s im Download (Empfehlung fürs Homeoffice: 50 Mbit/s)

## VPN einrichten (Schritt für Schritt)

1. **Self-Service-Portal** öffnen: <https://portal.leinetech.intern> → Softwarekatalog → "Cisco Secure Client" installieren (auf den meisten Geräten bereits vorinstalliert).
2. Client starten und als Gateway `vpn.leinetech.de` eintragen.
3. Mit Benutzername (`vorname.nachname`) und Passwort anmelden.
4. MFA-Push in der Authenticator-App bestätigen.
5. Nach erfolgreichem Aufbau erscheint das Schloss-Symbol in der Taskleiste; Netzlaufwerke (z. B. Projektlaufwerk `P:`) verbinden sich automatisch nach 1–2 Minuten.

## Split-Tunneling-Policy

LeineTech nutzt **Split-Tunneling**: Nur Traffic zu internen Ressourcen (`*.leinetech.intern`,
interne IP-Bereiche `10.20.0.0/16`) läuft durch den Tunnel. Microsoft 365, Teams, Zoom und
Software-Updates gehen **direkt ins Internet**, damit der Tunnel nicht überlastet wird.

> **Bekanntes Problem (Mai 2026):** Nach dem Update auf Secure Client 5.1.3 kann die
> Split-Tunnel-Konfiguration auf den Standard "Full Tunnel" zurückfallen. Symptom: Das gesamte
> Internet ist am Firmengerät plötzlich sehr langsam, Videocalls brechen ab, private Geräte im
> selben Heimnetz sind normal schnell. Lösung: VPN trennen, Client neu starten, neu verbinden —
> dabei wird das Profil neu geladen. Hilft das nicht: Ticket mit Kategorie **Netzwerk** eröffnen.

## Häufige Fehler und Lösungen

### Verbindungsaufbau bleibt bei 90 Prozent hängen, danach Timeout
1. Prüfen, ob ein **Captive Portal** aktiv ist (Hotel-/Bahn-WLAN): erst im Browser anmelden, dann VPN starten.
2. Client-Version prüfen (Hilfe → Info). Versionen unter 5.1 werden vom Gateway abgewiesen.
3. Router/Hotspot neu starten; alternativ Handy-Hotspot testen, um das lokale Netz auszuschließen.
4. Bleibt der Fehler bestehen: Ticket mit Uhrzeit des Versuchs und Client-Version eröffnen.

### Tunnel steht, aber interne Ressourcen (Laufwerke, DMS, Jira) nicht erreichbar
Typische Ursache ist DNS oder Routing, nicht die Anmeldung:
1. VPN trennen und neu verbinden (Profil wird neu geladen).
2. `nslookup dms.leinetech.intern` ausführen — kommt keine `10.20.x.x`-Adresse zurück, liegt ein DNS-Problem vor.
3. Ticket mit Kategorie **Netzwerk** eröffnen und die `nslookup`-Ausgabe anhängen.

### MFA-Push kommt nicht an
- Authenticator-App öffnen und manuell aktualisieren; alternativ den 6-stelligen Code eingeben.
- Bei neuem Handy: MFA über <https://passwort.leinetech.intern> neu registrieren.

## FAQ

**Darf ich das VPN aus dem Ausland nutzen?**
Ja, aus EU-Ländern ohne Einschränkung. Außerhalb der EU vorher das Security-Team über ein Ticket informieren (Compliance-Vorgabe).

**Warum ist Teams nicht über das VPN geschützt?**
Teams läuft per Split-Tunneling direkt über Microsoft — das ist gewollt und durch die M365-Verschlüsselung abgedeckt.

**Wie lange bleibt die Verbindung bestehen?**
Nach 12 Stunden oder 30 Minuten Inaktivität trennt das Gateway automatisch.

**Brauche ich VPN für E-Mail?**
Nein, Outlook/Exchange Online funktioniert ohne VPN. VPN wird nur für interne Systeme (Laufwerke, DMS, FinanzPro, Jira/GitLab self-hosted) benötigt.

**An wen wende ich mich bei dringenden VPN-Problemen?**
Service Desk, Hotline intern **-4242**. Reaktionszeiten siehe Artikel *IT-Support-Prozesse*.
