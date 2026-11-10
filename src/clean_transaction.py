"""Nettoyage de transaction.csv (branche feature/clean-transaction)."""
import pandas as pd

COLONNES = {"Date": "date", "Time": "heure", "Item Code": "item_code",
            "Quantity Sold (kilo)": "quantite_kg", "Unit Selling Price (RMB/kg)": "prix_vente",
            "Sale or Return": "type_ligne", "Discount (Yes/No)": "promo"}


def nettoyer(t):
    # Mise au format minimale, nécessaire aux jointures du pipeline.
    # TODO feature/clean-transaction : contrôles qualité (manquants, doublons, aberrants).
    t = t.rename(columns=COLONNES)
    t["date"] = pd.to_datetime(t["date"], format="%Y-%m-%d")
    t["promo"] = t["promo"].map({"Yes": True, "No": False})
    t["est_retour"] = t["type_ligne"].eq("return")
    return t.drop(columns="type_ligne")
