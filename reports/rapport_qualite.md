# Rapport qualité (généré par src/nettoyage.py)

| Étape | Contrôle | Résultat | Action |
|---|---|---|---|
| Chargement | transaction.csv | 878 503 lignes | lu en Bronze |
| Chargement | product.csv | 251 lignes | lu en Bronze |
| Chargement | price.csv | 55 982 lignes | lu en Bronze |
| Chargement | loss_rate.csv | 251 lignes | lu en Bronze |
| Types | Espaces insécables dans les catégories | 100 articles | remplacés par un espace normal |
| Doublons | price : clé (date, item_code) | 0 doublon | aucune action |
| Types | date texte -> date, promo Yes/No -> booléen | OK | convertis |
| Manquants | transaction : cellules vides | 0 | aucune action |
| Doublons | transaction : lignes identiques | 0 | aucune action |
| Doublons | transaction : même date + heure + article | 2 lignes | gardées : quantités différentes, deux pesées distinctes |
| Aberrants | retour sans quantité négative (ou l'inverse) | 0 | aucune action |
| Aberrants | quantité > Q3 + 1,5 × IQR (1.42 kg) | 10570 lignes | signalées (flag_qte_iqr), conservées |
| Aberrants | quantité > 50 kg (règle métier) | 1 ligne | signalée (flag_qte_extreme), à exclure des analyses |
| Aberrants | prix de vente <= 0 | 0 | aucune action |
| Jointure | transaction × price sur (date, item_code) | 878503 -> 878503 lignes | OK, aucune ligne dupliquée |
| Jointure | ventes sans prix d'achat (orphelins) | 0 | aucune action |
| Jointure | ventes sans catégorie (orphelins) | 0 | aucune action |
| Anomalies métier | vente sous le prix d'achat | 12660 lignes | signalées (flag_sous_prix_achat), conservées |
| Jointure | produits sans taux de perte | 0 | aucune action |
