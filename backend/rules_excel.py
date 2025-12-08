import pandas as pd

def load_excel_rules(path="zulassung.xlsx"):
    import pandas as pd

    xls = pd.ExcelFile(path)

    # --- TAB 1: Module + ECTS-Bereiche -----------------------------
    df_modules = pd.read_excel(xls, "Module")
    category_cols = [c for c in df_modules.columns if c != "Modulbezeichnung"]

    # 🔹 "x" oder "X" → 1, leere Felder → 0, Zahlen bleiben Zahlen
    for col in category_cols:
        df_modules[col] = (
            df_modules[col]
            .astype(str)
            .str.strip()
            .replace({"x": 1, "X": 1, "": 0, "nan": 0})
        )
        try:
            df_modules[col] = df_modules[col].astype(float)
        except ValueError:
            df_modules[col] = 0.0

        # 🔹 Jedes Modul zählt 5 ECTS → multiplizieren
        df_modules[col] = df_modules[col] * 5

    # 🔹 Summen pro Kategorie (in ECTS)
    module_ects = df_modules[category_cols].fillna(0).sum().to_dict()

    # --- TAB 2: Studiengänge ---------------------------------------
    df_programs = pd.read_excel(xls, "Studiengänge")

    programs = {}
    for program in df_programs["Studiengang"].unique():
        subset = df_programs[df_programs["Studiengang"] == program]
        ects_req = dict(zip(subset["Kategorie"], subset["Mindest-ECTS"]))

        programs[program] = {
            "ECTS_Anforderungen": ects_req
        }

    # --- TAB 3: Allgemeine Anforderungen ---------------------------
    df_general = pd.read_excel(xls, "Allgemein")
    general = dict(zip(df_general["Schlüssel"], df_general["Wert"]))

    # -------- Gesamtes Regelwerk zurückgeben ------------------------
    rules = {
        "Allgemein": general,
        "Studiengänge": programs,
        "Module_ECTS": module_ects
    }

    return rules


def get_general_requirements(rules):
    return rules["Allgemein"]


def get_program_requirements(rules, program):
    return rules["Studiengänge"].get(program)


def calculate_bachelor_ects(bachelor, studienart, vertiefung, filepath="zulassung.xlsx"):
    """
    Berechnet die ECTS je Kategorie für einen gegebenen Bachelorstudiengang
    auf Basis der Modulzusammensetzung und Modultabelle.
    """
    try:
        df_modules = pd.read_excel(filepath, sheet_name="Module")
        df_structure = pd.read_excel(filepath, sheet_name="Modulzusammensetzung")

        # 🔍 passende Zeile in der Struktur finden
        entry = df_structure[
            (df_structure["Bachelorstudiengang"].str.lower() == bachelor.lower()) &
            (df_structure["Studienart"].str.lower() == studienart.lower()) &
            (df_structure["Vertiefung"].str.lower() == vertiefung.lower())
        ]

        if entry.empty:
            return {}

        # Pflicht- und Wahlpflichtmodule extrahieren
        modules = []
        pflicht_raw = entry.iloc[0]["Pflichtmodule"]
        wahlpflicht_raw = entry.iloc[0]["Wahlpflichtmodule"]

        if isinstance(pflicht_raw, str):
            modules += [m.strip() for m in pflicht_raw.split(",") if m.strip()]
        if isinstance(wahlpflicht_raw, str):
            modules += [m.strip() for m in wahlpflicht_raw.split(",") if m.strip()]

        # Spaltennamen der Kategorien (alle außer 'Modul' und 'ECTS')
        categories = [col for col in df_modules.columns if col not in ["Modul", "ECTS"]]

        # Summiere ECTS je Kategorie
        ects_summary = {cat: 0 for cat in categories}

        for mod in modules:
            match = df_modules[df_modules["Modul"].str.lower() == mod.lower()]
            if not match.empty:
                ects = match.iloc[0]["ECTS"]
                for cat in categories:
                    if str(match.iloc[0][cat]).lower() == "x":
                        ects_summary[cat] += ects

        # Filtere nur Kategorien, die > 0 haben
        ects_summary = {k: v for k, v in ects_summary.items() if v > 0}

        return ects_summary

    except Exception as e:
        print(f"[Fehler bei ECTS-Berechnung]: {e}")
        return {}
