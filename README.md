# Calculateur chantier

Application Python autonome pour estimer des materiaux de travaux:

- pieces de structure 2 x 3, 2 x 4, 2 x 6 ou autre selon longueur, hauteur, espacement, longueur achetee, extras, pertes et prix;
- feuilles de gypse ou panneaux selon surface a couvrir, dimensions des feuilles, ouvertures, pertes et prix.
- plancher selon surface, retraits, couverture par boite, pertes et prix;
- peinture selon dimensions de piece, ouvertures, plafond, couches, couverture et prix;
- moulures ou plinthes selon perimetre, ouvertures, longueur des pieces, pertes et prix.

## Lancer

```powershell
python app.py
```

Puis ouvrir:

```text
http://localhost:8000
```

Dans cet environnement Codex, Python est aussi disponible ici:

```text
C:\Users\Jesen\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

## Lancer avec Docker

Construire l'image:

```powershell
docker build -t calculateur-chantier .
```

Lancer le conteneur:

```powershell
docker run --rm -p 8000:8000 --name calculateur-chantier calculateur-chantier
```

Puis ouvrir:

```text
http://localhost:8000
```

Avec Docker Compose:

```powershell
docker compose up --build
```

Pour le lancer en arriere-plan:

```powershell
docker compose up -d --build
```

Pour l'arreter:

```powershell
docker compose down
```

## Notes

Les calculs sont des estimations de chantier. Verifie toujours les normes locales, les ouvertures, les coins, les blocages, les pertes reelles et les produits exacts avant achat.
