"""Nettoyage de loss_rate.csv (branche feature/clean-loss-rate)."""
from journal import log

COLONNES = {"Item Code": "item_code", "Item Name": "nom_produit_perte", "Loss Rate (%)": "taux_perte_pct"}


def nettoyer(l):
    l = l.rename(columns=COLONNES)

    # Valeurs manquantes
    manquants = int(l.isna().sum().sum())
    log("Manquants", "loss_rate : cellules vides", f"{manquants}",
        "aucune action" if manquants == 0 else "à traiter")

    # Clé item_code : un seul taux par produit (relation 1-1 avec product)
    doublons = int(l.duplicated("item_code").sum())
    l = l.drop_duplicates("item_code")
    log("Doublons", "loss_rate : clé item_code", f"{doublons}",
        "aucune action" if doublons == 0 else "supprimés (première ligne gardée)")

    # Valeurs aberrantes : un taux de perte est un pourcentage, entre 0 et 100
    hors_bornes = ~l["taux_perte_pct"].between(0, 100)
    l["flag_taux_hors_bornes"] = hors_bornes
    log("Aberrants", "loss_rate : taux de perte hors de [0 ; 100] %", f"{int(hors_bornes.sum())}",
        "aucune action" if hors_bornes.sum() == 0 else "signalés (flag_taux_hors_bornes)")
    return l
