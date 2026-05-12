from __future__ import annotations

from backend.app.exports.dxf import export_dxf
from backend.app.exports.svg import export_svg


class DXFExporter:
    """Compatibility adapter for older scripts."""

    def export(self, pattern, model_name="AtelierCAD Patron T-shirt"):
        return export_dxf([_legacy_to_pattern_payload(pattern)], model_name)

    def export_svg(self, pattern):
        return export_svg(_legacy_to_pattern_payload(pattern))


def _legacy_to_pattern_payload(pattern: dict) -> dict:
    pieces = []
    for piece_id, piece in pattern.items():
        points = piece.get("points", [])
        if not points:
            continue
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        grain = piece.get("grainline") or [[0, 0], [0, 1]]
        pieces.append(
            {
                "id": piece_id,
                "name": piece.get("label", piece_id.upper()),
                "size": "M",
                "stitchPath": "M " + " L ".join(f"{x} {y}" for x, y in points) + " Z",
                "stitchPoints": points,
                "cutPoints": piece.get("cut_points", points),
                "grainline": {"start": grain[0], "end": grain[1], "label": "DROIT-FIL"},
                "notches": [
                    {"id": f"{piece_id}-{index}", "point": notch, "angle": 0, "kind": "single", "label": ""}
                    for index, notch in enumerate(piece.get("notches", []))
                ],
                "measurements": [],
                "labelPoint": [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2],
                "seamAllowance": 0,
                "areaCm2": 0,
                "cutAreaCm2": 0,
                "perimeterCm": 0,
                "bbox": {
                    "min_x": min(xs),
                    "min_y": min(ys),
                    "max_x": max(xs),
                    "max_y": max(ys),
                    "width": max(xs) - min(xs),
                    "height": max(ys) - min(ys),
                },
                "warnings": [],
                "metadata": {},
            }
        )
    return {"size": "M", "pieces": pieces, "validations": [], "metadata": {}, "bounds": {}}
