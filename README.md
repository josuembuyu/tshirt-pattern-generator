# AtelierCAD - Générateur de patrons T-shirt

AtelierCAD est une application web de CAO habillement pour construire de vrais patrons paramétriques de T-shirt. Le projet combine un moteur géométrique FastAPI et une interface React/TypeScript premium avec rendu SVG par calques.

## Fonctionnalités

- Génération cohérente des pièces : devant, dos, manche et bord-côte.
- Gradation XS à XXL avec tableau de mesures éditable et superposition multi-tailles.
- Lignes de couture construites en courbes de Bézier cubiques, puis échantillonnées en polylignes de production pour la validation et l'export.
- Lignes de coupe générées depuis une marge de couture configurable.
- Coloris et motifs textile paramétriques : uni, rayures, carreaux, pois, côte et chiné, avec échelle, orientation et intensité.
- Contrôles automatiques : auto-intersections, tête de manche vs emmanchure, coutures côté, coutures épaule et réduction du bord-côte.
- Exports DXF, SVG, dossier technique PDF et package ZIP avec annotations, métadonnées, coloris et informations matière.
- Sauvegarde et chargement de projets JSON.

## Stack

Backend :

- FastAPI
- Pydantic
- ezdxf
- shapely
- numpy / scipy
- reportlab

Frontend :

- React
- TypeScript
- Vite
- TailwindCSS
- Framer Motion
- Zustand
- Rendu SVG

## Structure

```text
backend/
  app/
    api/routes.py              endpoints FastAPI
    core/config.py             grille de tailles et configuration
    engine/geometry.py         courbes, échantillonnage, offsets, bornes
    engine/pattern.py          modèle des pièces de patron
    engine/validation.py       validation géométrique et coutures
    garments/tshirt.py         construction paramétrique T-shirt
    garments/registry.py       registre pour futurs vêtements
    exports/dxf.py             export DXF par calques
    exports/svg.py             export SVG annoté
    exports/techpack.py        dossier technique PDF
frontend/
  src/
    components/cad/            plan de travail SVG
    components/panels/         panneaux de commande
    lib/                       API et utilitaires géométriques
    store/                     état projet Zustand
    types/                     types TypeScript partagés
app.py                         point d'entrée FastAPI
pattern_generator.py           adaptateur de compatibilité
dxf_exporter.py                adaptateur de compatibilité
start.sh                       lance l'API et l'interface React
```

## Lancer en local

Quand vous êtes prêt à installer :

```bash
./venv/bin/pip install -r requirements.txt
npm install --prefix frontend
```

Puis :

```bash
./start.sh
```

Ou séparément :

```bash
./venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
npm --prefix frontend run dev
```

Ouvrir `http://localhost:5173`.

## API

- `GET /api/health`
- `GET /api/sizes`
- `POST /api/patterns/generate`
- `POST /api/exports/dxf`
- `POST /api/exports/svg`
- `POST /api/exports/pdf`
- `POST /api/exports/zip`
- `POST /api/projects/normalize`

Les anciens endpoints restent disponibles :

- `GET /api/size_chart`
- `POST /api/generate_pattern`
- `POST /api/export_dxf`
- `POST /api/export_svg`
- `POST /api/export_all_sizes`

## Notes géométriques

Les lignes visibles sont de vraies courbes de Bézier, pas des tracés décoratifs. Pour les contrôles industriels et l'export DXF, le backend échantillonne ces courbes avec une résolution contrôlée et valide les contours fermés avec Shapely. Le modèle reste donc paramétrique et éditable, tout en produisant une géométrie exploitable en CAO/FAO.

Le registre de vêtements est prêt pour ajouter ensuite hoodie, sweatshirt, raglan, polo, pantalon et autres bases.
