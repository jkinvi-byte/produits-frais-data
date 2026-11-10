# Rapport qualité (généré par src/pipeline.py)

| Étape | Contrôle | Résultat | Action |
|---|---|---|---|
| Chargement | transaction.csv | 878 503 lignes | lu en Bronze |
| Chargement | product.csv | 251 lignes | lu en Bronze |
| Chargement | price.csv | 55 982 lignes | lu en Bronze |
| Chargement | loss_rate.csv | 251 lignes | lu en Bronze |
| Jointure | transaction × price sur (date, item_code) | 878503 -> 878503 lignes | OK, aucune ligne dupliquée |
| Jointure | ventes sans prix d'achat (orphelins) | 0 | contrôlé |
| Jointure | ventes sans catégorie (orphelins) | 0 | contrôlé |
| Anomalies métier | vente sous le prix d'achat | 12660 lignes | signalées (flag_sous_prix_achat), conservées |
| Jointure | produits sans taux de perte | 0 | contrôlé |
