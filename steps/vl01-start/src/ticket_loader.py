import json
import os, sys
import requests

CACHE = None


def load_tickets(path="data/tickets.json", filter=None):
    global CACHE
    if CACHE != None:
        return CACHE
    try:
        f = open(path)
        data = json.load(f)
    except:
        data = []
    CACHE = data
    return data


def get_ticket(tid):
    tickets = load_tickets()
    for t in tickets:
        if t["id"] == tid:
            return t
    return None
