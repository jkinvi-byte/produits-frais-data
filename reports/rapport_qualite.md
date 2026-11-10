# Rapport qualité (généré par src/pipeline.py)

| Étape | Contrôle | Résultat | Action |
|---|---|---|---|
| Chargement | transaction.csv | 878 503 lignes | lu en Bronze |
| Types | transaction : date texte -> date, promo Yes/No -> booléen | OK | convertis |
| Manquants | transaction : cellules vides | 0 | aucune action |
| Doublons | transaction : lignes identiques | 0 | aucune action |
| Doublons | transaction : même date + heure + article | 2 lignes | gardées : quantités différentes, deux pesées distinctes |
| Aberrants | transaction : retour sans quantité négative (ou l'inverse) | 0 | aucune action |
| Aberrants | transaction : quantité > Q3 + 1,5 × IQR (1.42 kg) | 10570 lignes | signalées (flag_qte_iqr), conservées |
| Aberrants | transaction : quantité > 50 kg (règle métier) | 1 ligne | signalée (flag_qte_extreme), à exclure des analyses |
| Aberrants | transaction : prix de vente <= 0 | 0 | aucune action |
| Chargement | product.csv | 251 lignes | lu en Bronze |
| Types | product : espaces insécables dans les catégories | 100 articles | remplacés par un espace normal |
| Manquants | product : cellules vides | 0 | aucune action |
| Doublons | product : clé item_code | 0 | aucune action |
| Chargement | price.csv | 55 982 lignes | lu en Bronze |
| Types | price : date texte -> date | OK | convertie |
| Manquants | price : cellules vides | 0 | aucune action |
| Doublons | price : clé (date, item_code) | 0 | aucune action |
| Aberrants | price : prix d'achat <= 0 | 0 | aucune action |
| Chargement | loss_rate.csv | 251 lignes | lu en Bronze |
| Manquants | loss_rate : cellules vides | 0 | aucune action |
| Doublons | loss_rate : clé item_code | 0 | aucune action |
| Aberrants | loss_rate : taux de perte hors de [0 ; 100] % | 0 | aucune action |
| Jointure | transaction × price sur (date, item_code) | 878503 -> 878503 lignes | OK, aucune ligne dupliquée |
| Jointure | ventes sans prix d'achat (orphelins) | 0 | contrôlé |
| Jointure | ventes sans catégorie (orphelins) | 0 | contrôlé |
| Anomalies métier | vente sous le prix d'achat | 12660 lignes | signalées (flag_sous_prix_achat), conservées |
| Jointure | produits sans taux de perte | 0 | contrôlé |
