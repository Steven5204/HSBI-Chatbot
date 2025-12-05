import csv
from datetime import datetime

def log_event(event):
    with open("chatlog.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            event.get("user_id"),
            event.get("nutzerkategorie"),
            event.get("studiengang"),
            event.get("abschlussziel"),
            event.get("entscheidung"),
            event.get("completed")
        ])
