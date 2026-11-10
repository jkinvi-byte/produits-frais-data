"""Nettoyage de loss_rate.csv (branche feature/clean-loss-rate)."""

COLONNES = {"Item Code": "item_code", "Item Name": "nom_produit_perte", "Loss Rate (%)": "taux_perte_pct"}


def nettoyer(l):
    # Mise au format minimale, nécessaire aux jointures du pipeline.
    # TODO feature/clean-loss-rate : contrôles qualité (taux entre 0 et 100, doublons, manquants).
    return l.rename(columns=COLONNES)
