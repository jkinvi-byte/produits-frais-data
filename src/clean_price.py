"""Nettoyage de price.csv (branche feature/clean-price)."""
import pandas as pd
from journal import log

COLONNES = {"Date": "date", "Item Code": "item_code", "Wholesale Price (RMB/kg)": "prix_achat"}


def nettoyer(pr):
    pr = pr.rename(columns=COLONNES)

    # Types
    pr["date"] = pd.to_datetime(pr["date"], format="%Y-%m-%d")
    log("Types", "price : date texte -> date", "OK", "convertie")

    # Valeurs manquantes
    manquants = int(pr.isna().sum().sum())
    log("Manquants", "price : cellules vides", f"{manquants}",
        "aucune action" if manquants == 0 else "à traiter")

    # Clé primaire composée (date, item_code) : doit être unique,
    # sinon la jointure avec transaction duplique les ventes
    doublons = int(pr.duplicated(["date", "item_code"]).sum())
    pr = pr.drop_duplicates(["date", "item_code"])
    log("Doublons", "price : clé (date, item_code)", f"{doublons}",
        "aucune action" if doublons == 0 else "supprimés (premier prix gardé)")

    # Valeurs aberrantes
    prix_nuls = int((pr["prix_achat"] <= 0).sum())
    log("Aberrants", "price : prix d'achat <= 0", f"{prix_nuls}",
        "aucune action" if prix_nuls == 0 else "signalés")
    return pr
