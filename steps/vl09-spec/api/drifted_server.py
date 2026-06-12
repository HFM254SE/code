"""ABSICHTLICH von openapi.yaml abweichende Implementierung — für Lab-Teil 3.

Hier sind FÜNF Spec-Drifts versteckt. Findet sie (mit schemathesis und/oder
per Hand) und vergleicht mit `api/app.py` bzw. `api/openapi.yaml`. Lösung
steht weiter unten als Kommentar — erst selbst suchen!

    uvicorn api.drifted_server:app --port 8001
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.ticket_loader import load_tickets
from src.triage import classify_and_prioritize

app = FastAPI(title="LeineTech Ticket-API (drifted)", version="1.0.0")


class TicketEingabe(BaseModel):
    # DRIFT 1: 'von' fehlt komplett — die Spec verlangt es als Pflichtfeld.
    betreff: str = Field(min_length=1)
    text: str = Field(min_length=1)


class Ticket(TicketEingabe):
    id: str
    erstellt: str


class TriageErgebnis(BaseModel):
    id: str
    kategorie: str
    # DRIFT 2: Feld heißt hier 'prio' statt 'prioritaet' (Spec: 'prioritaet').
    prio: str


def _tickets() -> dict[str, dict]:
    return {t["id"]: t for t in load_tickets()}


@app.get("/tickets", tags=["tickets"])
def list_tickets(limit: int = 50):
    # DRIFT 3: Query-Parameter 'kategorie' aus der Spec fehlt.
    return list(load_tickets())[:limit]


@app.get("/tickets/{ticket_id}", response_model=Ticket, tags=["tickets"])
def get_ticket(ticket_id: str):
    ticket = _tickets().get(ticket_id)
    if ticket is None:
        # DRIFT 4: Liefert 400 statt des spezifizierten 404 bei Not-Found.
        raise HTTPException(status_code=400, detail="nicht da")
    return ticket


@app.post("/tickets/{ticket_id}/triage", response_model=TriageErgebnis, tags=["tickets"])
def triage_ticket(ticket_id: str):
    ticket = _tickets().get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} nicht gefunden")
    kategorie, prioritaet = classify_and_prioritize(ticket)
    return {"id": ticket_id, "kategorie": kategorie, "prio": prioritaet}


# DRIFT 5: POST /tickets (Ticket anlegen) und POST /tickets/{id}/escalate
#          aus der Spec fehlen hier ganz.

# ─────────────────────────────────────────────────────────────────────────
# Lösung (erst nach eigener Suche lesen):
#   1. POST /tickets: 'von' (Pflichtfeld) fehlt im Request-Schema.
#   2. POST /tickets/{id}/triage: Response-Feld 'prio' statt 'prioritaet'.
#   3. GET /tickets: Query-Parameter 'kategorie' fehlt.
#   4. GET /tickets/{id}: 400 statt 404 bei nicht gefundenem Ticket.
#   5. POST /tickets und POST /tickets/{id}/escalate fehlen komplett.
