from src.ticket_loader import load_tickets
from src.triage import triage_all
from src.stats import print_stats

tickets = load_tickets()
print("LeineTech Ticket-Triage")
print("Anzahl Tickets: " + str(len(tickets)))
results = triage_all(tickets)
for r in results:
    print(r["id"] + " | " + r["prioritaet"].upper().ljust(7) + " | " + r["kategorie"].ljust(10) + " | " + r["betreff"])
print_stats(results)
