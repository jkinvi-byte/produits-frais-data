"""Nettoyage de transaction.csv (branche feature/clean-transaction)."""
import pandas as pd
from journal import log

COLONNES = {"Date": "date", "Time": "heure", "Item Code": "item_code",
            "Quantity Sold (kilo)": "quantite_kg", "Unit Selling Price (RMB/kg)": "prix_vente",
            "Sale or Return": "type_ligne", "Discount (Yes/No)": "promo"}
SEUIL_METIER_KG = 50  # au-delà, une vente en magasin est jugée impossible


def nettoyer(t):
    t = t.rename(columns=COLONNES)

    # Types
    t["date"] = pd.to_datetime(t["date"], format="%Y-%m-%d")
    t["promo"] = t["promo"].map({"Yes": True, "No": False})
    t["est_retour"] = t["type_ligne"].eq("return")
    log("Types", "transaction : date texte -> date, promo Yes/No -> booléen", "OK", "convertis")

    # Valeurs manquantes
    manquants = int(t.isna().sum().sum())
    log("Manquants", "transaction : cellules vides", f"{manquants}",
        "aucune action" if manquants == 0 else "à traiter")

    # Doublons
    exacts = int(t.duplicated().sum())
    t = t.drop_duplicates()
    log("Doublons", "transaction : lignes identiques", f"{exacts}", "supprimées" if exacts else "aucune action")
    fonctionnels = int(t.duplicated(["date", "heure", "item_code"], keep=False).sum())
    log("Doublons", "transaction : même date + heure + article", f"{fonctionnels} lignes",
        "gardées : quantités différentes, deux pesées distinctes")

    # Cohérence : un retour a une quantité négative, une vente une quantité positive
    incoherents = int(((t["quantite_kg"] < 0) != t["est_retour"]).sum())
    log("Aberrants", "transaction : retour sans quantité négative (ou l'inverse)", f"{incoherents}",
        "aucune action" if incoherents == 0 else "signalés")

    # Valeurs aberrantes : on SIGNALE, on ne supprime pas
    q1, q3 = t.loc[~t["est_retour"], "quantite_kg"].quantile([0.25, 0.75])
    seuil_iqr = q3 + 1.5 * (q3 - q1)
    t["flag_qte_iqr"] = t["quantite_kg"] > seuil_iqr
    t["flag_qte_extreme"] = t["quantite_kg"] > SEUIL_METIER_KG
    log("Aberrants", f"transaction : quantité > Q3 + 1,5 × IQR ({seuil_iqr:.2f} kg)",
        f"{int(t['flag_qte_iqr'].sum())} lignes", "signalées (flag_qte_iqr), conservées")
    log("Aberrants", f"transaction : quantité > {SEUIL_METIER_KG} kg (règle métier)",
        f"{int(t['flag_qte_extreme'].sum())} ligne", "signalée (flag_qte_extreme), à exclure des analyses")
    prix_nuls = int((t["prix_vente"] <= 0).sum())
    log("Aberrants", "transaction : prix de vente <= 0", f"{prix_nuls}",
        "aucune action" if prix_nuls == 0 else "signalés")

    return t.drop(columns="type_ligne")
