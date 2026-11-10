"""Nettoyage de product.csv (branche feature/clean-product)."""

COLONNES = {"Item Code": "item_code", "Item Name": "nom_produit",
            "Category Code": "code_categorie", "Category Name": "categorie"}


def nettoyer(p):
    # Mise au format minimale, nécessaire aux jointures du pipeline.
    # TODO feature/clean-product : contrôles qualité (espaces cachés, doublons, manquants).
    return p.rename(columns=COLONNES)
