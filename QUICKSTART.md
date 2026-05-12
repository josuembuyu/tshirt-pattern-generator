# Démarrage rapide

## 1. Installer plus tard

Quand vous êtes prêt à installer les dépendances :

```bash
./venv/bin/pip install -r requirements.txt
npm install --prefix frontend
```

Si le cache npm local pose problème :

```bash
npm_config_cache=/tmp/ateliercad-npm-cache npm install --prefix frontend
```

## 2. Démarrer

```bash
./start.sh
```

L'API tourne sur `http://localhost:8000`.

L'interface CAO React tourne sur `http://localhost:5173`.

## 3. Utiliser

1. Choisir la taille active de XS à XXL.
2. Modifier les mesures ou le tableau de gradation.
3. Choisir la coupe, le col, la longueur de manche et la marge de couture.
4. Définir le coloris tissu, le coloris motif, le type de motif, son échelle, son orientation et son intensité.
5. Activer ou masquer les calques : matière, couture, découpe, droit-fil, crans, étiquettes et mesures.
6. Exporter en DXF, SVG, dossier technique PDF ou ZIP.

## Test rapide

```bash
./venv/bin/python - <<'PY'
from backend.app.core.config import DEFAULT_SIZE_CHART
from backend.app.models import Measurements, GarmentOptions
from backend.app.garments.tshirt import TShirtPatternGenerator

pattern = TShirtPatternGenerator(
    Measurements(**DEFAULT_SIZE_CHART["M"]),
    GarmentOptions(fit="regular", neckline="round", sleeve="short"),
    "M",
).generate().to_payload()

print(pattern["size"], len(pattern["pieces"]))
print([v for v in pattern["validations"] if v["severity"] != "ok"])
PY
```
