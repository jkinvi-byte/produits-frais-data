"""Journal des contrôles qualité, partagé par tous les modules."""

journal = []


def log(etape, controle, resultat, action):
    journal.append({"Étape": etape, "Contrôle": controle, "Résultat": resultat, "Action": action})
    print(f"[{etape}] {controle} : {resultat} -> {action}")
