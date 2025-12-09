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
def log_interaction(user_id, abschlussziel, studiengang, nutzerkategorie, entscheidung, status="abgeschlossen", progress=100):
    """Loggt eine Chatinteraktion (Start, Zwischenschritt oder Abschluss)."""
    now = datetime.now().isoformat()
    entry = [now, user_id, abschlussziel, studiengang, nutzerkategorie, entscheidung, status, progress]

    # Datei anlegen, falls sie noch nicht existiert
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["timestamp", "user_id", "abschlussziel", "studiengang", "nutzerkategorie", "entscheidung", "status", "progress"])
        writer.writerow(entry)


# === Reporting-Funktion ===
def generate_report(days: int = 30):
    """
    Liest die Logdatei (chatbot_logs.csv mit Headerzeile) ein und berechnet Kennzahlen
    für das Dashboard: Nutzer, abgeschlossene Sessions, Abbruchquote, Top-Programme, Nutzertypen.
    """
    log_file = os.path.join(os.path.dirname(__file__), "chatbot_log.csv")

    if not os.path.exists(log_file):
        print(f"[Report] ⚠️ Logdatei nicht gefunden unter: {log_file}")
        return {
            "period_days": days,
            "total_users": 0,
            "completed": 0,
            "dropped": 0,
            "dropout_rate": 0,
            "beliebteste_studiengänge": [],
            "nutzertypen": {}
        }

    # 🧩 CSV einlesen (mit Header, UTF-8, BOM-Support)
    try:
        df = pd.read_csv(
            log_file,
            sep=",",
            encoding="utf-8-sig",
            on_bad_lines="skip"
        )
    except Exception as e:
        print(f"[Report] ❌ Fehler beim Einlesen der Logdatei: {e}")
        return {
            "period_days": days,
            "total_users": 0,
            "completed": 0,
            "dropped": 0,
            "dropout_rate": 0,
            "beliebteste_studiengänge": [],
            "nutzertypen": {}
        }

    # 🔍 Debug
    print(f"[Report] {len(df)} Zeilen geladen")
    print(df.head(3).to_string())

    # 🕓 Timestamps sicher parsen
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    # 🧹 Zeitraumfilter (letzte X Tage)
    cutoff = datetime.now() - timedelta(days=days)
    df = df[df["timestamp"] >= cutoff]
    print(f"[Report] {len(df)} Zeilen nach Filter (letzte {days} Tage)")

    if df.empty:
        print("[Report] ⚠️ Keine Daten im angegebenen Zeitraum")
        return {
            "period_days": days,
            "total_users": 0,
            "completed": 0,
            "dropped": 0,
            "dropout_rate": 0,
            "beliebteste_studiengänge": [],
            "nutzertypen": {}
        }

    # === Grundkennzahlen ===
    total_users = df["user_id"].nunique()
    completed_users = df[df["status"] == "abgeschlossen"]["user_id"].nunique()
    dropped_users = total_users - completed_users
    dropout_rate = round((dropped_users / total_users * 100), 2) if total_users > 0 else 0

    # === Beliebteste Studiengänge (nur Master, nur abgeschlossene Sessions) ===
    df["abschlussziel"] = df["abschlussziel"].astype(str).str.strip().str.lower()
    df["studiengang"] = df["studiengang"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip().str.lower()

    # Nur abgeschlossene Sessions pro Nutzer behalten
    df_last = df.sort_values("timestamp").groupby("user_id").tail(1)
    df_completed = df_last[df_last["status"] == "abgeschlossen"]

    # Nur Master-Einträge zählen
    master_df = df_completed[df_completed["abschlussziel"].str.contains("master", case=False, na=False)]

    if not master_df.empty:
        top_programs = (
            master_df["studiengang"]
            .replace("Unbekannt", pd.NA)
            .dropna()
            .value_counts()
            .head(5)
            .reset_index()
            .values.tolist()
        )
    else:
        top_programs = []

    # === Nutzerkategorien zählen ===
    df["nutzerkategorie"] = df["nutzerkategorie"].astype(str).str.strip()
    nutzertypen = (
        df["nutzerkategorie"]
        .replace("Unbekannt", pd.NA)
        .dropna()
        .value_counts()
        .to_dict()
    )

    # 🧾 Debug-Ausgabe
    print(f"[Report] Nutzer insgesamt: {total_users}")
    print(f"[Report] Abgeschlossen: {completed_users}, Abgebrochen: {dropped_users} ({dropout_rate}%)")
    print(f"[Report] Top Programme: {list(top_programs)}")
    print(f"[Report] Nutzertypen: {nutzertypen}")

    # === Dashboard-Response ===
    return {
        "period_days": days,
        "total_users": int(total_users),
        "completed": int(completed_users),
        "dropped": int(dropped_users),
        "dropout_rate": dropout_rate,
        "beliebteste_studiengänge": list(top_programs),
        "nutzertypen": nutzertypen
    }