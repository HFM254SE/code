"""Laden der LeineTech-Support-Tickets aus der JSON-Datenbasis."""

import json
from functools import lru_cache
from pathlib import Path

DEFAULT_TICKET_PATH = Path("data/tickets.json")


@lru_cache(maxsize=1)
def load_tickets(path: Path = DEFAULT_TICKET_PATH) -> tuple[dict, ...]:
    """Lädt alle Tickets aus der JSON-Datei.

    Liefert ein unveränderliches Tupel, damit der Cache nicht versehentlich
    von Aufrufern mutiert werden kann.

    Raises:
        FileNotFoundError: wenn die Ticket-Datei nicht existiert.
        json.JSONDecodeError: wenn die Datei kein gültiges JSON enthält.
    """
    with open(path, encoding="utf-8") as file:
        return tuple(json.load(file))


def get_ticket(ticket_id: str, path: Path = DEFAULT_TICKET_PATH) -> dict | None:
    """Liefert das Ticket mit der gegebenen ID oder None."""
    for ticket in load_tickets(path):
        if ticket["id"] == ticket_id:
            return ticket
    return None
