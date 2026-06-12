import re
import os
from src.ticket_loader import load_tickets


def classify_and_prioritize(t):
    TXT = (t.get("betreff", "") + " " + t.get("text", "")).lower()
    kategorie = "Software"
    found = False
    if found == False:
        for w in ["rechnung", "kosten", "vertrag", "tarif", "zahlung", "buchhaltung"]:
            if w in TXT:
                kategorie = "Abrechnung"
                found = True
                break
    if found == False:
        for w in ["passwort", "login", "anmelden", "konto", "gesperrt", "zugriff", "berechtigung"]:
            if w in TXT:
                kategorie = "Zugang"
                found = True
                break
    if found == False:
        for w in ["wlan", "vpn", "internet", "netzwerk", "verbindung", "lan"]:
            if w in TXT:
                kategorie = "Netzwerk"
                found = True
                break
    if found == False:
        for w in ["laptop", "drucker", "monitor", "tastatur", "maus", "docking", "akku", "headset"]:
            if w in TXT:
                kategorie = "Hardware"
                found = True
                break
    if found == False:
        for w in ["absturz", "fehlermeldung", "update", "installation", "lizenz", "programm", "anwendung"]:
            if w in TXT:
                kategorie = "Software"
                found = True
                break
    prioritaet = "mittel"
    found2 = False
    if found2 == False:
        for w in ["dringend", "sofort", "produktion", "ausfall", "nichts geht", "komplett"]:
            if w in TXT:
                prioritaet = "hoch"
                found2 = True
                break
    if found2 == False:
        for w in ["frage", "gelegentlich", "kein stress", "wunsch", "irgendwann"]:
            if w in TXT:
                prioritaet = "niedrig"
                found2 = True
                break
    return kategorie, prioritaet


def triage_all(tickets=None):
    if tickets == None:
        tickets = load_tickets()
    results = []
    for t in tickets:
        k, p = classify_and_prioritize(t)
        results.append({"id": t["id"], "betreff": t["betreff"], "kategorie": k, "prioritaet": p})
    return results
