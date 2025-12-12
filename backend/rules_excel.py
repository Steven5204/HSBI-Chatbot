import pandas as pd

def get_vertiefungen_for(studiengang: str, studienart: str = None) -> list:
    """
    Gibt alle Vertiefungen aus der Excel-Datei zurück,
    die zu einem bestimmten Bachelorstudiengang (und optional Studienart) gehören.
    Funktioniert robust gegen Leerzeichen, Groß-/Kleinschreibung und Tippfehler.
    """
    import pandas as pd

    try:
        df = pd.read_excel("zulassung.xlsx", sheet_name="Modulzusammensetzung")

        # Normalisiere Texte (entferne Leerzeichen, Kleinbuchstaben)
        df["Bachelorstudiengang"] = df["Bachelorstudiengang"].astype(str).str.strip().str.lower()
        df["Studienart"] = df["Studienart"].astype(str).str.strip().str.lower()
        df["Vertiefung"] = df["Vertiefung"].astype(str).str.strip()

        studiengang_norm = str(studiengang).strip().lower()
        studienart_norm = str(studienart).strip().lower() if studienart else None

        # Filter anwenden
        subset = df[df["Bachelorstudiengang"] == studiengang_norm]
        if studienart_norm:
            subset = subset[subset["Studienart"] == studienart_norm]

        vertiefungen = subset["Vertiefung"].dropna().unique().tolist()

        # Filtere leere Strings heraus
        vertiefungen = [v for v in vertiefungen if v and v.strip() != "" and v.lower() != "nan"]

        print(f"[Excel] Vertiefungen gefunden für {studiengang} ({studienart}): {vertiefungen}")
        return sorted(vertiefungen)

    except Exception as e:
        print(f"[Fehler in get_vertiefungen_for]: {e}")
        return []


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


def calculate_bachelor_ects(studiengang: str, studienart: str, vertiefung: str):
    """
    Berechnet die aufsummierten ECTS für einen bestimmten Bachelorstudiengang
    basierend auf der Excel-Tabelle 'Modulzusammensetzung' und 'Module'.
    Erkennt automatisch Schreibvarianten (Pflichtmodule, Prlichtmodule etc.)
    und rechnet dynamisch nach Kategorien (Mathematik, Technik, Informatik, ...).
    """

    try:
        # === 1️⃣ Modulzusammensetzung laden
        df_zus = pd.read_excel("zulassung.xlsx", sheet_name="Modulzusammensetzung")
        df_zus.columns = [str(c).strip().lower() for c in df_zus.columns]

        # Spalten dynamisch finden
        col_bachelor = next((c for c in df_zus.columns if "bachelor" in c), None)
        col_studienart = next((c for c in df_zus.columns if "studienart" in c), None)
        col_vertiefung = next((c for c in df_zus.columns if "vertiefung" in c), None)
        col_module = next((c for c in df_zus.columns if "pflicht" in c or "modul" in c), None)

        if not all([col_bachelor, col_studienart, col_vertiefung, col_module]):
            raise KeyError("Fehlende Spalten (Bachelorstudiengang / Studienart / Vertiefung / Pflichtmodule)")

        # Filter anwenden
        subset = df_zus[
            (df_zus[col_bachelor].astype(str).str.strip().str.lower() == studiengang.strip().lower())
            & (df_zus[col_studienart].astype(str).str.strip().str.lower() == studienart.strip().lower())
            & (df_zus[col_vertiefung].astype(str).str.strip().str.lower() == vertiefung.strip().lower())
        ]

        if subset.empty:
            print(f"[ECTS] Keine Einträge für {studiengang} / {studienart} / {vertiefung}")
            return {}

        # === 2️⃣ Modulnamen extrahieren
        module_list = []
        for mods in subset[col_module].dropna():
            for mod in str(mods).split(","):
                module_list.append(mod.strip())

        if not module_list:
            print(f"[ECTS] Keine Module gefunden für {studiengang} ({vertiefung})")
            return {}

        # === 3️⃣ Modulliste laden und filtern
        df_mod = pd.read_excel("zulassung.xlsx", sheet_name="Module")
        df_mod.columns = [str(c).strip().lower() for c in df_mod.columns]

        col_modname = next((c for c in df_mod.columns if "modul" in c), None)
        if not col_modname:
            raise KeyError("Spalte mit Modulnamen nicht gefunden (z. B. 'Modulbezeichnung').")

        # Nur relevante Module behalten (Groß-/Kleinschreibung ignorieren)
        module_names = [m.strip().lower() for m in module_list]
        df_mod[col_modname] = df_mod[col_modname].astype(str).str.strip().str.lower()
        df_filtered = df_mod[df_mod[col_modname].isin(module_names)]

        # === 4️⃣ Relevante ECTS-Kategorien automatisch erkennen
        category_cols = [
            c for c in df_filtered.columns
            if any(x in c for x in ["mathematik", "technik", "naturwissenschaft", "betriebswirtschaft", "informatik", "elektrotechnik"])
        ]

        if not category_cols:
            print("[ECTS] Keine ECTS-Kategorien erkannt.")
            return {}

        # === 5️⃣ 'x' → 5 ECTS konvertieren und summieren
        df_filtered[category_cols] = df_filtered[category_cols].applymap(
            lambda x: 5 if str(x).strip().lower() == "x" else 0
        )
        ects_sum = df_filtered[category_cols].sum().to_dict()

        print(f"[ECTS-Berechnung erfolgreich] {studiengang} / {vertiefung}: {ects_sum}")
        return ects_sum

    except Exception as e:
        print(f"[Fehler bei ECTS-Berechnung]: {e}")
        return {}
