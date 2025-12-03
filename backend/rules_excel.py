import pandas as pd

def load_excel_rules(path="zulassung.xlsx"):
    xls = pd.ExcelFile(path)

    # --- TAB 1: Module + ECTS-Bereiche -----------------------------
    df_modules = pd.read_excel(xls, "Module")
    category_cols = [c for c in df_modules.columns if c != "Modulbezeichnung"]

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
