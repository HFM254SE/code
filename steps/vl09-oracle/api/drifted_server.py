"""Implementierung mit ABSICHTLICHEN Abweichungen von api/openapi.yaml.

Zielscheibe fuer das Konformitaets-Gate in Teil 2 des Labs. Diese Datei ist
kein Suchspiel: **welche** Abweichungen hier stecken, steht auf der Folie und
im Lab-Sheet. Die Aufgabe ist, das Gate zu bauen, das sie findet — und das
gleichzeitig auf `api/app.py` gruen bleibt.

    python -m uvicorn api.drifted_server:app --port 8001
    # nur falls ihr sie laufen sehen wollt; das Gate braucht keinen Server
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.ticket_loader import load_tickets
from src.triage import classify_and_prioritize

app = FastAPI(title="LeineTech Ticket-API (drifted)", version="1.0.0")


class TicketEingabe(BaseModel):
    # Pflichtfeld 'von' aus der Spec fehlt hier.
    betreff: str = Field(min_length=1)
    text: str = Field(min_length=1)


class Ticket(TicketEingabe):
    id: str
    erstellt: str


class TriageErgebnis(BaseModel):
    id: str
    kategorie: str
    prio: str


def _tickets() -> dict[str, dict]:
    return {t["id"]: t for t in load_tickets()}


@app.get("/tickets", tags=["tickets"])
def list_tickets(limit: int = 50):
    return list(load_tickets())[:limit]


@app.post("/tickets", response_model=Ticket, status_code=201, tags=["tickets"])
def create_ticket(eingabe: TicketEingabe):
    store = _tickets()
    next_num = max((int(tid[2:]) for tid in store), default=1000) + 1
    return {
        "id": f"T-{next_num}",
        "betreff": eingabe.betreff,
        "text": eingabe.text,
        "erstellt": "2026-05-31",
    }


@app.get("/tickets/{ticket_id}", response_model=Ticket, tags=["tickets"])
def get_ticket(ticket_id: str):
    ticket = _tickets().get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=400, detail="nicht da")
    return ticket


@app.post("/tickets/{ticket_id}/triage", response_model=TriageErgebnis, tags=["tickets"])
def triage_ticket(ticket_id: str):
    ticket = _tickets().get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} nicht gefunden")
    kategorie, prioritaet = classify_and_prioritize(ticket)
    return {"id": ticket_id, "kategorie": kategorie, "prio": prioritaet}


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}
