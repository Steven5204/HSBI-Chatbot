import pandas as pd

def get_vertiefungen_for(bachelorstudiengang: str, studienart: str, path="zulassung.xlsx"):
    """
    Liest aus der Excel-Datei (Registerkarte 'Modulzusammensetzung') alle verfügbaren Vertiefungsrichtungen
    für den angegebenen Bachelorstudiengang und die Studienart.
    Gibt eine Liste der Vertiefungen zurück (z. B. ['Logistik', 'Technik']).
    """
    try:
        xls = pd.ExcelFile(path)
        df = pd.read_excel(xls, "Modulzusammensetzung")

        # 🔧 Spaltennamen prüfen
        expected_cols = ["Bachelorstudiengang", "Studienart", "Vertiefung"]
        for col in expected_cols:
            if col not in df.columns:
                raise KeyError(f"Spalte '{col}' fehlt in der Excel-Datei.")

        # 🔍 Filter auf passenden Studiengang + Studienart
        mask = (
            (df["Bachelorstudiengang"].astype(str).str.lower() == str(bachelorstudiengang).strip().lower())
            & (df["Studienart"].astype(str).str.lower() == str(studienart).strip().lower())
        )
        matching = df.loc[mask]

        # 🎯 Alle Vertiefungen extrahieren
        vertiefungen = sorted(
            [v for v in matching["Vertiefung"].dropna().unique() if str(v).strip() != ""]
        )

        print(f"[Excel] Vertiefungen gefunden für {bachelorstudiengang} ({studienart}): {vertiefungen}")
        return vertiefungen

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


def get_bachelor_ects(bachelorstudiengang, studienart, vertiefung, df_modules, df_zusammensetzung):
    """
    Liefert für einen bestimmten Bachelorstudiengang, Studienart und Vertiefung
    die ECTS-Summe pro Kategorie, basierend auf den Pflichtmodulen aus der Excel-Tabelle.
    """

    # 🔹 Relevante Zeile im Tabellenblatt "Modulzusammensetzung" finden
    subset = df_zusammensetzung[
        (df_zusammensetzung["Bachelorstudiengang"].str.lower() == bachelorstudiengang.lower()) &
        (df_zusammensetzung["Studienart"].str.lower() == studienart.lower()) &
        (df_zusammensetzung["Vertiefung"].str.lower() == vertiefung.lower())
    ]

    if subset.empty:
        print("⚠️ Keine passende Zeile für diesen Studiengang gefunden.")
        return {}

    # 🔹 Liste der Pflichtmodule extrahieren
    module_list = subset.iloc[0]["Pflichtmodule"]
    if isinstance(module_list, str):
        module_list = [m.strip() for m in module_list.split(",")]
    else:
        module_list = []

    # 🔹 Initialisiere ECTS-Summen
    ects_sum = {
        "Mathematik": 0,
        "Technik": 0,
        "Naturwissenschaft": 0,
        "Betriebswirtschaft": 0,
        "Informatik": 0,
        "Elektrotechnik": 0
    }

    # 🔹 Pro Modul prüfen, welche Kategorien betroffen sind
    for modul in module_list:
        row = df_modules[df_modules["Modulbezeichnung"].str.lower() == modul.lower().strip()]
        if not row.empty:
            for cat in ects_sum.keys():
                try:
                    ects_sum[cat] += float(row.iloc[0][cat])
                except Exception:
                    continue

    return ects_sum


def get_general_requirements(rules):
    return rules["Allgemein"]


def get_program_requirements(rules, program):
    return rules["Studiengänge"].get(program)


def calculate_bachelor_ects(studiengang: str, studienart: str, vertiefung: str):
    """
    Berechnet die aufsummierten ECTS für einen bestimmten Bachelorstudiengang
    basierend auf der Excel-Tabelle 'Modulzusammensetzung'.
    """
    try:
        df = pd.read_excel("zulassung.xlsx", sheet_name="Modulzusammensetzung")

        # 🔍 Filter nach Kombination Studiengang / Studienart / Vertiefung
        subset = df[
            (df["Bachelorstudiengang"].str.lower() == studiengang.lower())
            & (df["Studienart"].str.lower() == studienart.lower())
            & (df["Vertiefung"].str.lower() == vertiefung.lower())
        ]

        if subset.empty:
            print(f"[ECTS] Keine Daten für {studiengang} / {studienart} / {vertiefung}")
            return None

        # 🔹 Spaltenname „Prlichtmodule“ verwenden (Achtung Schreibfehler)
        if "Pflichtmodule" not in subset.columns:
            raise KeyError("Spalte 'Pflichtmodule' nicht in Excel gefunden.")

        module_list = []
        for mods in subset["Pflichtmodule"].dropna():
            for mod in str(mods).split(","):
                module_list.append(mod.strip())

        if not module_list:
            print(f"[ECTS] Keine Module gefunden für {studiengang}.")
            return None

        # 🔹 Module-Tabelle laden
        df_modules = pd.read_excel("zulassung.xlsx", sheet_name="Module")

        # 🔹 Nur die relevanten Module filtern
        df_filtered = df_modules[df_modules["Modulbezeichnung"].isin(module_list)]

        # 🔹 Spalten außer „Modulbezeichnung“ sind Kategorien (Mathematik, Technik etc.)
        category_cols = [c for c in df_filtered.columns if c != "Modulbezeichnung"]

        # 🔹 Jede Zelle enthält „x“ → 5 ECTS Punkte
        df_filtered[category_cols] = df_filtered[category_cols].applymap(lambda x: 5 if str(x).strip().lower() == "x" else 0)

        # 🔹 Summe pro Kategorie berechnen
        ects_sum = df_filtered[category_cols].sum().to_dict()

        print(f"[ECTS-Berechnung erfolgreich] {studiengang} / {vertiefung}: {ects_sum}")
        return ects_sum

    except Exception as e:
        print(f"[Fehler bei ECTS-Berechnung]: {e}")
        return None
