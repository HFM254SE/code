# Netzwerk und WLAN

Stand: Mai 2026

## WLAN-Netze im Büro

| SSID | Zweck | Zugang |
|---|---|---|
| **LT-Corp** | Firmengeräte | automatisch per Zertifikat (802.1X, via Intune) |
| **LT-Guest** | Gäste, private Geräte | Voucher, 24 h gültig |
| **LT-IoT** | Konferenztechnik, Sensorik | nur durch die IT |

### LT-Corp (Firmengeräte)

Firmengeräte verbinden sich automatisch — das Zertifikat wird bei der Geräteeinrichtung
installiert. Es gibt **kein** Passwort zum Eintippen. Verbindet sich ein Gerät nicht:

1. WLAN aus- und einschalten, einmal neu starten.
2. Prüfen, ob das Gerät kürzlich länger offline war (Zertifikate laufen nach 12 Monaten ab und erneuern sich nur online).
3. Ticket eröffnen, Kategorie **Netzwerk**, mit Gerätenummer und Etage.

### LT-Guest (Gäste und private Geräte)

- Zugang über **personalisierte Voucher**: Der Empfang oder jede Mitarbeiterin/jeder Mitarbeiter mit Portalzugang kann Voucher erstellen (<https://portal.leinetech.intern> → "Gästezugang").
- Voucher gelten **24 Stunden** ab erster Nutzung; für mehrtägige Workshops können Voucher mit bis zu 5 Tagen Laufzeit erstellt werden.
- Es gibt bewusst **kein zentrales Gäste-Passwort** — jeder Gast erhält einen eigenen Voucher (Nachvollziehbarkeit, Compliance).
- Für Veranstaltungen mit mehr als 20 Gästen bitte 3 Werktage vorher ein Ticket eröffnen, dann erstellt die IT Sammel-Voucher und prüft die Kapazität der Access Points.

## Störungen im Büro-WLAN

Typisches Bild: Verbindung bricht regelmäßig ab und baut sich neu auf, oft auf einer ganzen
Etage. Häufige Ursache ist ein gestörter Access-Point-Uplink.

- **LED-Codes der Access Points:** grün = normal, **orange blinkend = Uplink-Störung**, rot = Hardware-Defekt.
- Bitte im Ticket immer angeben: Etage, ungefähre Position, LED-Farbe, Anzahl betroffener Personen — das beschleunigt die Eingrenzung erheblich.
- Sind mehrere Personen betroffen, behandelt die IT die Störung mit erhöhter Priorität.

## LAN-Dosen und Verkabelung

- Dosenbeschriftung: `<Etage>.<Raum>-<Port>`, z. B. `3.2.07-B` = 3. OG, Raum 2.07, Port B.
- Nicht jede Dose ist aktiv gepatcht. Tote Dose (Link-LED am Endgerät bleibt aus) bitte per Ticket melden, Kategorie **Netzwerk**, mit der vollständigen Dosennummer.
- Patchen/Durchmessen erledigt die IT in der Regel innerhalb von 2 Werktagen; mit Terminbindung (z. B. Kundenworkshop) bitte das Datum ins Ticket schreiben.
- Eigenmächtiges Umstecken im Netzwerkschrank ist nicht zulässig.

## Anforderungen für Heimarbeit

- Internetanschluss mit mindestens **16 Mbit/s** (empfohlen: 50 Mbit/s) und stabilem WLAN oder LAN.
- Zugriff auf interne Systeme ausschließlich über VPN (siehe Artikel *VPN-Zugang*).
- Am privaten Router sind **keine** Sonderkonfigurationen (Portfreigaben o. Ä.) nötig.
- Performance-Probleme, die nur am Firmengerät auftreten, deuten auf die VPN-/Split-Tunnel-Konfiguration hin — siehe bekannte Probleme im VPN-Artikel.

## FAQ

**Wie lautet das WLAN-Passwort für LT-Corp?**
Es gibt keins — Firmengeräte authentifizieren sich per Zertifikat. Private Geräte gehören in LT-Guest.

**Kann mein privates Handy ins LT-Corp?**
Nein. Private Geräte nutzen LT-Guest, dienstliche Handys werden per Intune automatisch eingebunden.

**Wer bekommt Voucher-Rechte für LT-Guest?**
Alle festangestellten Mitarbeitenden haben die Funktion im Portal automatisch.

**Im Besprechungsraum ist das WLAN überlastet — was tun?**
Für Demos und Workshops die LAN-Dosen nutzen (stabiler) und bei Bedarf vorab per Ticket patchen lassen.

**An wen wende ich mich bei einem kompletten Netzwerkausfall?**
Hotline intern **-4242** (vom Handy: +49 511 4790-4242). Komplettausfälle gelten als Priorität hoch.
