"""
Pipeline complet : Bronze (data/raw) -> Silver (data/silver) -> Gold (data/gold).

Chaque fichier source a son propre module de nettoyage, développé sur sa
branche feature :
    clean_transaction.py  -> feature/clean-transaction
    clean_product.py      -> feature/clean-product
    clean_price.py        -> feature/clean-price
    clean_loss_rate.py    -> feature/clean-loss-rate

Ce fichier assemble les 4 modules et consolide le modèle en étoile.
Lancer depuis la racine du repo :
    python src/pipeline.py
"""
from pathlib import Path
import pandas as pd

from journal import journal, log
import clean_transaction, clean_product, clean_price, clean_loss_rate

RACINE = Path(__file__).resolve().parent.parent
RAW, SILVER, GOLD, REPORTS = (RACINE / "data/raw", RACINE / "data/silver",
                              RACINE / "data/gold", RACINE / "reports")


def charger(nom):
    """Lit un CSV brut. Item Code et Category Code sont des identifiants : lus en texte."""
    df = pd.read_csv(RAW / f"{nom}.csv", encoding="utf-8-sig",
                     dtype={"Item Code": str, "Category Code": str})
    log("Chargement", f"{nom}.csv", f"{len(df):,} lignes".replace(",", " "), "lu en Bronze")
    return df


def consolider(t, p, pr, l):
    n0 = len(t)
    f = (t.merge(pr, on=["date", "item_code"], how="left", validate="many_to_one")
          .merge(p[["item_code", "categorie"]], on="item_code", how="left", validate="many_to_one"))
    log("Jointure", "transaction × price sur (date, item_code)", f"{n0} -> {len(f)} lignes",
        "OK, aucune ligne dupliquée" if n0 == len(f) else "ERREUR : lignes dupliquées")
    assert n0 == len(f), "La jointure a dupliqué des lignes"
    log("Jointure", "ventes sans prix d'achat (orphelins)", f"{f['prix_achat'].isna().sum()}", "contrôlé")
    log("Jointure", "ventes sans catégorie (orphelins)", f"{f['categorie'].isna().sum()}", "contrôlé")

    f["ca"] = f["quantite_kg"] * f["prix_vente"]
    f["cout_achat"] = f["quantite_kg"] * f["prix_achat"]
    f["marge_brute"] = f["ca"] - f["cout_achat"]
    f["flag_sous_prix_achat"] = f["prix_vente"] < f["prix_achat"]
    log("Anomalies métier", "vente sous le prix d'achat", f"{f['flag_sous_prix_achat'].sum()} lignes",
        "signalées (flag_sous_prix_achat), conservées")
    f.insert(0, "transaction_id", range(1, len(f) + 1))
    colonnes_flags = [c for c in f.columns if c.startswith("flag_")]
    fait_ventes = f[["transaction_id", "date", "heure", "item_code", "quantite_kg", "prix_vente",
                     "prix_achat", "promo", "est_retour", "ca", "cout_achat", "marge_brute"] + colonnes_flags]

    dim_produit = p.merge(l[["item_code", "taux_perte_pct"]], on="item_code", how="left", validate="one_to_one")
    log("Jointure", "produits sans taux de perte", f"{dim_produit['taux_perte_pct'].isna().sum()}", "contrôlé")

    dim_date = pd.DataFrame({"date": pd.date_range(f["date"].min(), f["date"].max(), freq="D")})
    dim_date["annee"], dim_date["mois"] = dim_date["date"].dt.year, dim_date["date"].dt.month
    dim_date["jour_semaine"] = dim_date["date"].dt.dayofweek + 1
    dim_date["periode"] = pd.cut(dim_date["date"],
                                 [pd.Timestamp("2000-01-01"), pd.Timestamp("2021-07-01"),
                                  pd.Timestamp("2022-07-01"), pd.Timestamp("2023-07-01")],
                                 right=False, labels=["Antérieur", "N-1", "N"]).astype(str)
    return fait_ventes, dim_produit, dim_date


def ecrire(t, p, pr, l, fait_ventes, dim_produit, dim_date):
    for d in (SILVER, GOLD, REPORTS):
        d.mkdir(parents=True, exist_ok=True)
    t.to_csv(SILVER / "transaction_clean.csv.gz", index=False)
    p.to_csv(SILVER / "product_clean.csv", index=False)
    pr.to_csv(SILVER / "price_clean.csv.gz", index=False)
    l.to_csv(SILVER / "loss_rate_clean.csv", index=False)
    fait_ventes.to_csv(GOLD / "fait_ventes.csv.gz", index=False)
    dim_produit.to_csv(GOLD / "dim_produit.csv", index=False)
    dim_date.to_csv(GOLD / "dim_date.csv", index=False)

    rapport = pd.DataFrame(journal)
    lignes = ["# Rapport qualité (généré par src/pipeline.py)", "",
              "| " + " | ".join(rapport.columns) + " |", "|" + "---|" * len(rapport.columns)]
    lignes += ["| " + " | ".join(map(str, r)) + " |" for r in rapport.itertuples(index=False)]
    (REPORTS / "rapport_qualite.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"\nRapport : {REPORTS / 'rapport_qualite.md'}")


if __name__ == "__main__":
    t = clean_transaction.nettoyer(charger("transaction"))
    p = clean_product.nettoyer(charger("product"))
    pr = clean_price.nettoyer(charger("price"))
    l = clean_loss_rate.nettoyer(charger("loss_rate"))
    fait_ventes, dim_produit, dim_date = consolider(t, p, pr, l)
    ecrire(t, p, pr, l, fait_ventes, dim_produit, dim_date)
