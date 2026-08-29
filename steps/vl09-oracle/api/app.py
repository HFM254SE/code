"""Referenz-Implementierung der LeineTech Ticket-API — konform zu openapi.yaml.

Das ist der Soll-Zustand: Dieser Server hält sich exakt an die Spec. In
Lab-Teil 3 vergleicht ihr ihn mit `drifted_server.py`, der absichtlich
abweicht. Gebaut mit FastAPI, weil FastAPI die OpenAPI-Spec aus dem Code
selbst generiert (`/docs`, `/openapi.json`) — so lässt sich Drift direkt
maschinell prüfen.

    python -m uvicorn api.app:app --reload
    # Doku unter http://localhost:8000/docs
"""

import re
from enum import Enum

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field, field_validator

from src.summarize import CATEGORIES, PRIORITIES  # eine Quelle der Wahrheit
from src.ticket_loader import load_tickets
from src.triage import classify_and_prioritize

app = FastAPI(title="LeineTech Ticket-API", version="1.0.0")

# Kategorien aus src/ als Enum, damit FastAPI den Query-Parameter validiert
# wie die Spec es verlangt (Schema "Kategorie" ist dort ein Enum).
KategorieEnum = Enum("KategorieEnum", {k: k for k in CATEGORIES}, type=str)

# In-Memory-Store: beim Start aus data/tickets.json geladen; POST legt neue
# Tickets hier ab, damit sie danach per GET abrufbar sind (Spec-Versprechen!).
_STORE: dict[str, dict] = {t["id"]: t for t in load_tickets()}


# "format: email" ist zweideutig — Pydantic akzeptiert z. B. IDN-Domains
# (münchen.de), der JSON-Schema-Format-Check vieler Tools nicht. Die Spec
# nagelt es deshalb per Pattern fest, und wir prüfen exakt dasselbe Pattern.
EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"


class TicketEingabe(BaseModel):
    von: EmailStr
    betreff: str = Field(min_length=1)
    text: str = Field(min_length=1)

    @field_validator("von")
    @classmethod
    def _von_wie_in_der_spec(cls, v: str) -> str:
        if not re.fullmatch(EMAIL_PATTERN, v):
            raise ValueError("E-Mail muss dem Pattern der Spec entsprechen")
        return v


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


def _require(ticket_id: str) -> dict:
    ticket = _STORE.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} nicht gefunden")
    return ticket


@app.get("/tickets", response_model=list[Ticket], tags=["tickets"])
def list_tickets(
    request: Request,
    kategorie: KategorieEnum | None = None,
    limit: int = Query(50, ge=1, le=100),  # Grenzen wie in der Spec (1–100)
):
    # Strikt wie die Spec: unbekannte Query-Parameter ablehnen statt still
    # ignorieren (FastAPI-Default wäre ignorieren).
    unbekannt = set(request.query_params) - {"kategorie", "limit"}
    if unbekannt:
        raise HTTPException(
            status_code=422,
            detail=[
                {"loc": ["query", name], "msg": "Unbekannter Parameter", "type": "extra_forbidden"}
                for name in sorted(unbekannt)
            ],
        )
    tickets = list(_STORE.values())
    if kategorie:
        tickets = [t for t in tickets if classify_and_prioritize(t)[0] == kategorie.value]
    return tickets[:limit]


@app.post("/tickets", response_model=Ticket, status_code=201, tags=["tickets"])
def create_ticket(eingabe: TicketEingabe):
    next_num = max((int(tid[2:]) for tid in _STORE), default=1000) + 1
    new = {
        "id": f"T-{next_num}",
        "von": eingabe.von,
        "betreff": eingabe.betreff,
        "text": eingabe.text,
        "erstellt": "2026-05-31",  # Demo: feste Eingangsdatum-Stub
    }
    _STORE[new["id"]] = new
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
