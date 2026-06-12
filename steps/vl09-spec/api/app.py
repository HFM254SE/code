"""Referenz-Implementierung der LeineTech Ticket-API — konform zu openapi.yaml.

Das ist der Soll-Zustand: Dieser Server hält sich exakt an die Spec. In
Lab-Teil 3 vergleicht ihr ihn mit `drifted_server.py`, der absichtlich
abweicht. Gebaut mit FastAPI, weil FastAPI die OpenAPI-Spec aus dem Code
selbst generiert (`/docs`, `/openapi.json`) — so lässt sich Drift direkt
maschinell prüfen.

    uvicorn api.app:app --reload
    # Doku unter http://localhost:8000/docs
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from src.summarize import CATEGORIES, PRIORITIES  # eine Quelle der Wahrheit
from src.ticket_loader import load_tickets
from src.triage import classify_and_prioritize

app = FastAPI(title="LeineTech Ticket-API", version="1.0.0")

DATA = Path(__file__).resolve().parent.parent / "data" / "tickets.json"


class TicketEingabe(BaseModel):
    von: EmailStr
    betreff: str = Field(min_length=1)
    text: str = Field(min_length=1)


class Ticket(TicketEingabe):
    id: str = Field(pattern=r"^T-\d{4}$")
    erstellt: str


class TriageErgebnis(BaseModel):
    id: str
    kategorie: str
    prioritaet: str


class EskalationErgebnis(BaseModel):
    id: str
    status: str
    grund: str


class Eskalation(BaseModel):
    grund: str = Field(min_length=3)


def _tickets() -> dict[str, dict]:
    return {t["id"]: t for t in load_tickets()}


def _require(ticket_id: str) -> dict:
    ticket = _tickets().get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} nicht gefunden")
    return ticket


@app.get("/tickets", response_model=list[Ticket], tags=["tickets"])
def list_tickets(kategorie: str | None = None, limit: int = 50):
    tickets = list(load_tickets())
    if kategorie:
        tickets = [t for t in tickets if classify_and_prioritize(t)[0] == kategorie]
    return tickets[:limit]


@app.post("/tickets", response_model=Ticket, status_code=201, tags=["tickets"])
def create_ticket(eingabe: TicketEingabe):
    existing = _tickets()
    next_num = max((int(tid[2:]) for tid in existing), default=1000) + 1
    new = {
        "id": f"T-{next_num}",
        "von": eingabe.von,
        "betreff": eingabe.betreff,
        "text": eingabe.text,
        "erstellt": "2026-05-31",  # Demo: feste Eingangsdatum-Stub
    }
    return new


@app.get("/tickets/{ticket_id}", response_model=Ticket, tags=["tickets"])
def get_ticket(ticket_id: str):
    return _require(ticket_id)


@app.post("/tickets/{ticket_id}/triage", response_model=TriageErgebnis, tags=["tickets"])
def triage_ticket(ticket_id: str):
    ticket = _require(ticket_id)
    kategorie, prioritaet = classify_and_prioritize(ticket)
    assert kategorie in CATEGORIES and prioritaet in PRIORITIES
    return {"id": ticket_id, "kategorie": kategorie, "prioritaet": prioritaet}


@app.post(
    "/tickets/{ticket_id}/escalate",
    response_model=EskalationErgebnis,
    status_code=202,
    tags=["tickets"],
)
def escalate_ticket(ticket_id: str, eskalation: Eskalation):
    _require(ticket_id)
    return {"id": ticket_id, "status": "eskaliert", "grund": eskalation.grund}
