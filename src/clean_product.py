"""Nettoyage de product.csv (branche feature/clean-product)."""
from journal import log

COLONNES = {"Item Code": "item_code", "Item Name": "nom_produit",
            "Category Code": "code_categorie", "Category Name": "categorie"}


def nettoyer_texte(s):
    """Remplace les espaces insécables (invisibles) et retire les espaces en trop."""
    return s.str.replace(" ", " ", regex=False).str.strip()


def nettoyer(p):
    p = p.rename(columns=COLONNES)

    # Espaces cachés : la catégorie « Flower/Leaf Vegetables » contient un espace insécable
    nb_nbsp = int(p["categorie"].str.contains(" ").sum())
    p["categorie"] = nettoyer_texte(p["categorie"])
    p["nom_produit"] = nettoyer_texte(p["nom_produit"])
    log("Types", "product : espaces insécables dans les catégories", f"{nb_nbsp} articles",
        "remplacés par un espace normal")

    # Valeurs manquantes
    manquants = int(p.isna().sum().sum())
    log("Manquants", "product : cellules vides", f"{manquants}",
        "aucune action" if manquants == 0 else "à traiter")

    # Clé primaire item_code : doit être unique (dimension produit)
    doublons = int(p.duplicated("item_code").sum())
    p = p.drop_duplicates("item_code")
    log("Doublons", "product : clé item_code", f"{doublons}",
        "aucune action" if doublons == 0 else "supprimés (première ligne gardée)")
    return p
