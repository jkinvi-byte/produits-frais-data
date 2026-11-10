"""Nettoyage de price.csv (branche feature/clean-price)."""
import pandas as pd

COLONNES = {"Date": "date", "Item Code": "item_code", "Wholesale Price (RMB/kg)": "prix_achat"}


def nettoyer(pr):
    # Mise au format minimale, nécessaire aux jointures du pipeline.
    # TODO feature/clean-price : contrôles qualité (clé unique, prix aberrants).
    pr = pr.rename(columns=COLONNES)
    pr["date"] = pd.to_datetime(pr["date"], format="%Y-%m-%d")
    return pr
