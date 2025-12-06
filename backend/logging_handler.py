import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter

LOG_FILE = "chatbot_log.csv"

# 🔹 Sicherstellen, dass Logdatei existiert
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "user_id", "abschlussziel", "studiengang", "entscheidung"])


# === Logging-Funktion ===
def log_interaction(user_id: str, abschlussziel: str, studiengang: str,nutzerkategorie:str, entscheidung: str):
    """
    Schreibt eine Interaktion in das CSV-Logfile.
    """
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            user_id,
            abschlussziel,
            studiengang,
            nutzerkategorie,
            entscheidung
        ])


# === Reporting-Funktion ===
def generate_report(days: int = 30):
    """
    Erstellt eine Nutzungsstatistik aus chatbot_log.csv
    für den angegebenen Zeitraum (Standard: 30 Tage).
    """
    import pandas as pd
    from datetime import datetime, timedelta

    try:
        df = pd.read_csv("chatbot_log.csv", header=None)
    except FileNotFoundError:
        return {"error": "Keine Log-Datei gefunden."}
    except pd.errors.EmptyDataError:
        return {"error": "Log-Datei ist leer."}

    # 🧠 Flexible Spaltenzuweisung (abhängig von CSV-Länge)
    if df.shape[1] == 6:
        df.columns = [
            "timestamp",
            "user_id",
            "abschlussziel",
            "studiengang",
            "nutzerkategorie",  # ✅ korrigiert!
            "entscheidung"
        ]
    elif df.shape[1] == 5:
        df.columns = [
            "timestamp",
            "user_id",
            "abschlussziel",
            "studiengang",
            "entscheidung"
        ]
        df["nutzerkategorie"] = "Unbekannt"  # alte Zeilen mit Platzhalter auffüllen
    else:
        return {"error": f"Unerwartete Spaltenanzahl: {df.shape[1]}"}

    # 🔹 Zeitfilterung
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    cutoff_date = datetime.now() - timedelta(days=days)
    df = df[df["timestamp"] >= cutoff_date]

    if df.empty:
        return {"info": f"Keine Daten im gewählten Zeitraum ({days} Tage)."}

    # 🔹 Auswertungen
    total_users = df["user_id"].nunique()
    successful = (df["entscheidung"].str.lower() == "ja").sum()
    top_programs = df["studiengang"].value_counts().head(5).reset_index().values.tolist()
    top_masters = (
        df[df["abschlussziel"].str.lower() == "master"]["studiengang"]
        .value_counts().head(5).reset_index().values.tolist()
    )
    category_counts = df["nutzerkategorie"].value_counts().to_dict()

    # 🔹 Ergebnis zurückgeben
    return {
        "zeitraum_tage": days,
        "anzahl_nutzer": int(total_users),
        "erfolgreiche_bewerbungen": int(successful),
        "beliebteste_studiengänge": top_programs,
        "beliebteste_masterstudiengänge": top_masters,
        "nutzertypen": category_counts
    }