# Passwort und Konto

Stand: Mai 2026

Jede Mitarbeiterin und jeder Mitarbeiter hat genau ein zentrales Benutzerkonto
(`vorname.nachname`), das für Windows/macOS, E-Mail, VPN, Jira, GitLab und die
Fachanwendungen gilt (Single Sign-On über Entra ID).

## Passwort-Richtlinie

- Mindestens **14 Zeichen**, keine Wiederverwendung der letzten 10 Passwörter
- Kein erzwungener regelmäßiger Wechsel; Wechsel nur bei Verdacht auf Kompromittierung
- Passwort-Manager (Bitwarden, Firmenlizenz) wird ausdrücklich empfohlen

## Passwort-Reset im Self-Service

1. <https://passwort.leinetech.intern> öffnen (funktioniert auch ohne VPN, z. B. vom Handy).
2. Benutzernamen eingeben und Identität per **MFA** (Authenticator-App) oder hinterlegter privater Wiederherstellungs-Mail bestätigen.
3. Neues Passwort vergeben — es gilt sofort für alle angeschlossenen Systeme.

> Wichtig: Der Self-Service funktioniert nur, wenn MFA **vorher** registriert wurde.
> Ohne registrierte MFA hilft nur der Service Desk (Hotline intern **-4242**) mit
> Identitätsprüfung per Videocall oder persönlich am IT-Service-Point (Raum 1.08).

Läuft die Self-Service-Seite ins Leere oder lädt nicht, bitte einen anderen Browser oder das
Smartphone (Mobilfunknetz statt Firmen-WLAN) testen und andernfalls ein Ticket eröffnen.

## Kontosperrung nach Fehlversuchen

- Nach **5 fehlgeschlagenen Anmeldeversuchen** wird das Konto automatisch für **30 Minuten** gesperrt.
- Die Sperre läuft entweder automatisch ab oder kann über die Self-Service-Entsperrung auf <https://passwort.leinetech.intern> aufgehoben werden.
- Greift die Self-Service-Entsperrung nicht (z. B. weil zusätzlich ein Sicherheitsflag gesetzt wurde), entsperrt der Service Desk das Konto nach Identitätsprüfung. Solche Fälle bitte telefonisch unter **-4242** melden — komplett gesperrte Konten gelten als dringend.
- Wiederholte Sperrungen ohne eigenes Zutun bitte immer melden: Das kann auf einen Angriffsversuch hindeuten.

## MFA-Pflicht

- MFA ist für **alle** Konten verpflichtend (Microsoft Authenticator, alternativ FIDO2-Hardware-Token auf Antrag).
- Registrierung und Verwaltung der Faktoren: <https://passwort.leinetech.intern> → "Sicherheitsinformationen".
- Bei Handywechsel die MFA **vor** dem Zurücksetzen des alten Geräts auf das neue übertragen.

## Namensänderung (z. B. Heirat)

1. Die Personalabteilung meldet die Namensänderung an die IT (kein eigenes Ticket nötig).
2. Der Benutzername wird umgestellt (`vorname.neuername`); der alte Benutzername wird deaktiviert.
3. Die IT teilt den neuen Benutzernamen per SMS an die hinterlegte Mobilnummer und über die Führungskraft mit.
4. Erste Anmeldung mit dem neuen Benutzernamen und dem bisherigen Passwort; danach MFA neu bestätigen.

> Kommt man nach der Umstellung in **kein** System mehr, ist meist die Synchronisation
> hängengeblieben — das ist ein dringender Fall für den Service Desk (Kategorie **Zugang**).

## Berechtigungen auf Ordner und Systeme

- Berechtigungen auf Projektordner (DMS, Netzlaufwerke) werden per Ticket beantragt (Kategorie **Zugang**).
- Erforderlich ist die **Freigabe der Teamleitung** (formlos per Mail genügt, bitte ans Ticket anhängen).
- Standard-Bearbeitungszeit: 1–2 Werktage nach vorliegender Freigabe.

## Onboarding neuer Mitarbeitender

- Neue Konten (Benutzerkonto, Postfach, Jira/GitLab) beantragt die Führungskraft per Ticket, Kategorie **Zugang**, spätestens **5 Werktage vor Startdatum**.
- Grundlage ist die Onboarding-Checkliste im Wiki; Hardware bitte separat bestellen (siehe Artikel *Hardware-Bestellung*).

## FAQ

**Ich habe mein Passwort vergessen — muss ich anrufen?**
Nein, der Self-Service unter <https://passwort.leinetech.intern> reicht in fast allen Fällen.

**Mein Konto sperrt sich ständig von selbst. Woran liegt das?**
Häufig ein altes Passwort in einem gespeicherten WLAN-Profil oder einer Mail-App auf dem Handy. Alle gespeicherten Anmeldungen aktualisieren; sonst Ticket eröffnen.

**Kann ich MFA ablehnen?**
Nein, MFA ist ohne Ausnahme verpflichtend (Beschluss der Geschäftsführung, Q1 2025).

**Wer sieht meine privaten Wiederherstellungsdaten?**
Nur das Identity-Team; die Daten werden ausschließlich für die Kontowiederherstellung genutzt.
