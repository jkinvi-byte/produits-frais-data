"""
Nettoyage et consolidation des ventes de produits frais.

Bronze (data/raw)  ->  Silver (data/silver)  ->  Gold (data/gold)

Lancer depuis la racine du repo :
    python src/nettoyage.py
"""
from pathlib import Path
import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
RAW, SILVER, GOLD, REPORTS = (RACINE / "data/raw", RACINE / "data/silver",
                              RACINE / "data/gold", RACINE / "reports")
journal = []  # chaque contrôle alimente le rapport qualité


def log(etape, controle, resultat, action):
    journal.append({"Étape": etape, "Contrôle": controle, "Résultat": resultat, "Action": action})
    print(f"[{etape}] {controle} : {resultat} -> {action}")


# ---------------------------------------------------------------------------
# 1. Chargement (Bronze) : item_code lu en texte dès la lecture
# ---------------------------------------------------------------------------
def charger():
    lire = dict(encoding="utf-8-sig", dtype={"Item Code": str, "Category Code": str})
    t = pd.read_csv(RAW / "transaction.csv", **lire)
    p = pd.read_csv(RAW / "product.csv", **lire)
    pr = pd.read_csv(RAW / "price.csv", **lire)
    l = pd.read_csv(RAW / "loss_rate.csv", **lire)
    for nom, df in [("transaction", t), ("product", p), ("price", pr), ("loss_rate", l)]:
        log("Chargement", f"{nom}.csv", f"{len(df):,} lignes".replace(",", " "), "lu en Bronze")
    return t, p, pr, l


# ---------------------------------------------------------------------------
# 2. Nettoyage (Bronze -> Silver)
# ---------------------------------------------------------------------------
def nettoyer_texte(s):
    """Supprime les espaces insécables et les espaces en trop."""
    return s.str.replace(" ", " ", regex=False).str.strip()


def nettoyer_product(p):
    p = p.rename(columns={"Item Code": "item_code", "Item Name": "nom_produit",
                          "Category Code": "code_categorie", "Category Name": "categorie"})
    nb_nbsp = p["categorie"].str.contains(" ").sum()
    p["categorie"] = nettoyer_texte(p["categorie"])
    p["nom_produit"] = nettoyer_texte(p["nom_produit"])
    log("Types", "Espaces insécables dans les catégories", f"{nb_nbsp} articles", "remplacés par un espace normal")
    return p


def nettoyer_loss(l):
    l = l.rename(columns={"Item Code": "item_code", "Item Name": "nom_produit_perte",
                          "Loss Rate (%)": "taux_perte_pct"})
    return l


def nettoyer_price(pr):
    pr = pr.rename(columns={"Date": "date", "Item Code": "item_code",
                            "Wholesale Price (RMB/kg)": "prix_achat"})
    pr["date"] = pd.to_datetime(pr["date"], format="%Y-%m-%d")
    doublons = pr.duplicated(["date", "item_code"]).sum()
    log("Doublons", "price : clé (date, item_code)", f"{doublons} doublon", "aucune action" if doublons == 0 else "supprimés")
    pr = pr.drop_duplicates(["date", "item_code"])
    return pr


def nettoyer_transaction(t):
    t = t.rename(columns={"Date": "date", "Time": "heure", "Item Code": "item_code",
                          "Quantity Sold (kilo)": "quantite_kg",
                          "Unit Selling Price (RMB/kg)": "prix_vente",
                          "Sale or Return": "type_ligne", "Discount (Yes/No)": "promo"})
    # Types
    t["date"] = pd.to_datetime(t["date"], format="%Y-%m-%d")
    t["promo"] = t["promo"].map({"Yes": True, "No": False})
    t["est_retour"] = t["type_ligne"].eq("return")
    log("Types", "date texte -> date, promo Yes/No -> booléen", "OK", "convertis")

    # Valeurs manquantes
    manquants = int(t.isna().sum().sum())
    log("Manquants", "transaction : cellules vides", f"{manquants}", "aucune action" if manquants == 0 else "à traiter")

    # Doublons
    exacts = t.duplicated().sum()
    t = t.drop_duplicates()
    log("Doublons", "transaction : lignes identiques", f"{exacts}", "supprimées" if exacts else "aucune action")
    fonctionnels = t.duplicated(["date", "heure", "item_code"], keep=False).sum()
    log("Doublons", "transaction : même date + heure + article", f"{fonctionnels} lignes",
        "gardées : quantités différentes, deux pesées distinctes")

    # Cohérence des retours : quantité négative <=> retour
    incoherents = ((t["quantite_kg"] < 0) != t["est_retour"]).sum()
    log("Aberrants", "retour sans quantité négative (ou l'inverse)", f"{incoherents}", "aucune action" if incoherents == 0 else "signalés")

    # Valeurs aberrantes : on SIGNALE, on ne supprime pas
    q1, q3 = t.loc[~t["est_retour"], "quantite_kg"].quantile([0.25, 0.75])
    seuil_iqr = q3 + 1.5 * (q3 - q1)
    t["flag_qte_iqr"] = t["quantite_kg"] > seuil_iqr
    t["flag_qte_extreme"] = t["quantite_kg"] > 50  # règle métier : > 50 kg pour un client en magasin
    log("Aberrants", f"quantité > Q3 + 1,5 × IQR ({seuil_iqr:.2f} kg)", f"{t['flag_qte_iqr'].sum()} lignes",
        "signalées (flag_qte_iqr), conservées")
    log("Aberrants", "quantité > 50 kg (règle métier)", f"{t['flag_qte_extreme'].sum()} ligne",
        "signalée (flag_qte_extreme), à exclure des analyses")
    prix_nuls = (t["prix_vente"] <= 0).sum()
    log("Aberrants", "prix de vente <= 0", f"{prix_nuls}", "aucune action" if prix_nuls == 0 else "signalés")
    return t.drop(columns="type_ligne")


# ---------------------------------------------------------------------------
# 3. Consolidation (Silver -> Gold) : modèle en étoile
# ---------------------------------------------------------------------------
def consolider(t, p, pr, l):
    n0 = len(t)
    f = (t.merge(pr, on=["date", "item_code"], how="left", validate="many_to_one")
          .merge(p[["item_code", "categorie"]], on="item_code", how="left", validate="many_to_one"))
    log("Jointure", "transaction × price sur (date, item_code)", f"{n0} -> {len(f)} lignes",
        "OK, aucune ligne dupliquée" if n0 == len(f) else "ERREUR : lignes dupliquées")
    assert n0 == len(f), "La jointure a dupliqué des lignes"

    sans_prix = f["prix_achat"].isna().sum()
    sans_cat = f["categorie"].isna().sum()
    log("Jointure", "ventes sans prix d'achat (orphelins)", f"{sans_prix}", "aucune action" if sans_prix == 0 else "à traiter")
    log("Jointure", "ventes sans catégorie (orphelins)", f"{sans_cat}", "aucune action" if sans_cat == 0 else "à traiter")

    # Mesures
    f["ca"] = f["quantite_kg"] * f["prix_vente"]
    f["cout_achat"] = f["quantite_kg"] * f["prix_achat"]
    f["marge_brute"] = f["ca"] - f["cout_achat"]
    f["flag_sous_prix_achat"] = f["prix_vente"] < f["prix_achat"]
    log("Anomalies métier", "vente sous le prix d'achat", f"{f['flag_sous_prix_achat'].sum()} lignes",
        "signalées (flag_sous_prix_achat), conservées")

    f.insert(0, "transaction_id", range(1, len(f) + 1))
    fait_ventes = f[["transaction_id", "date", "heure", "item_code", "quantite_kg", "prix_vente",
                     "prix_achat", "promo", "est_retour", "ca", "cout_achat", "marge_brute",
                     "flag_qte_iqr", "flag_qte_extreme", "flag_sous_prix_achat"]]

    # dim_produit = product + loss_rate (relation 1-1)
    dim_produit = p.merge(l[["item_code", "taux_perte_pct"]], on="item_code", how="left", validate="one_to_one")
    log("Jointure", "produits sans taux de perte", f"{dim_produit['taux_perte_pct'].isna().sum()}", "aucune action")

    # dim_date
    dates = pd.DataFrame({"date": pd.date_range(f["date"].min(), f["date"].max(), freq="D")})
    dates["annee"], dates["mois"] = dates["date"].dt.year, dates["date"].dt.month
    dates["jour_semaine"] = dates["date"].dt.dayofweek + 1
    dates["periode"] = pd.cut(dates["date"],
                              [pd.Timestamp("2000-01-01"), pd.Timestamp("2021-07-01"),
                               pd.Timestamp("2022-07-01"), pd.Timestamp("2023-07-01")],
                              right=False, labels=["Antérieur", "N-1", "N"]).astype(str)
    return fait_ventes, dim_produit, dates


# ---------------------------------------------------------------------------
# 4. Écriture et rapport
# ---------------------------------------------------------------------------
def ecrire(t, p, pr, fait_ventes, dim_produit, dim_date):
    for d in (SILVER, GOLD, REPORTS):
        d.mkdir(parents=True, exist_ok=True)
    t.to_csv(SILVER / "transaction_clean.csv.gz", index=False)
    p.to_csv(SILVER / "product_clean.csv", index=False)
    pr.to_csv(SILVER / "price_clean.csv.gz", index=False)
    fait_ventes.to_csv(GOLD / "fait_ventes.csv.gz", index=False)
    dim_produit.to_csv(GOLD / "dim_produit.csv", index=False)
    dim_date.to_csv(GOLD / "dim_date.csv", index=False)

    rapport = pd.DataFrame(journal)
    lignes = ["# Rapport qualité (généré par src/nettoyage.py)", "",
              "| " + " | ".join(rapport.columns) + " |", "|" + "---|" * len(rapport.columns)]
    lignes += ["| " + " | ".join(map(str, r)) + " |" for r in rapport.itertuples(index=False)]
    (REPORTS / "rapport_qualite.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"\nRapport : {REPORTS / 'rapport_qualite.md'}")


if __name__ == "__main__":
    t, p, pr, l = charger()
    p, l, pr, t = nettoyer_product(p), nettoyer_loss(l), nettoyer_price(pr), nettoyer_transaction(t)
    fait_ventes, dim_produit, dim_date = consolider(t, p, pr, l)
    ecrire(t, p, pr, fait_ventes, dim_produit, dim_date)
