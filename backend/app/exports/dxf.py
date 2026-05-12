from __future__ import annotations

from io import BytesIO
from tempfile import NamedTemporaryFile

import ezdxf
from ezdxf.enums import TextEntityAlignment


LAYER_COLORS = {
    "COUTURE": 7,
    "DECOUPE": 2,
    "DROIT_FIL": 3,
    "CRANS": 1,
    "MESURES": 4,
    "ANNOTATION": 6,
    "META": 8,
}


def export_dxf(patterns: list[dict], model_name: str = "AtelierCAD Patron T-shirt", appearance: dict | None = None) -> bytes:
    appearance = appearance or {}
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 5  # centimeters
    msp = doc.modelspace()
    for layer, color in LAYER_COLORS.items():
        if layer not in doc.layers:
            doc.layers.add(layer, color=color)

    y_cursor = 0.0
    for pattern in patterns:
        x_cursor = 0.0
        size = pattern["size"]
        msp.add_text(
            f"{model_name} | TAILLE {size}",
            dxfattribs={"layer": "META", "height": 3.5},
        ).set_placement((x_cursor, y_cursor - 8), align=TextEntityAlignment.LEFT)
        if appearance:
            msp.add_text(
                f"MATIERE {appearance.get('base_color', '')} | MOTIF {appearance.get('motif', 'none')} {appearance.get('accent_color', '')}",
                dxfattribs={"layer": "META", "height": 2.3},
            ).set_placement((x_cursor, y_cursor - 12), align=TextEntityAlignment.LEFT)
        for piece in pattern["pieces"]:
            box = piece["bbox"]
            x_offset = x_cursor - box["min_x"]
            y_offset = y_cursor - box["min_y"]
            stitch = [(x + x_offset, y + y_offset) for x, y in piece["stitchPoints"]]
            cut = [(x + x_offset, y + y_offset) for x, y in piece["cutPoints"]]
            msp.add_lwpolyline(stitch, close=True, dxfattribs={"layer": "COUTURE"})
            msp.add_lwpolyline(cut, close=True, dxfattribs={"layer": "DECOUPE"})
            grain = piece["grainline"]
            msp.add_line(
                (grain["start"][0] + x_offset, grain["start"][1] + y_offset),
                (grain["end"][0] + x_offset, grain["end"][1] + y_offset),
                dxfattribs={"layer": "DROIT_FIL"},
            )
            for notch in piece["notches"]:
                nx, ny = notch["point"][0] + x_offset, notch["point"][1] + y_offset
                depth = 1.4 if notch["kind"] == "single" else 2.1
                msp.add_lwpolyline(
                    [(nx - 0.8, ny), (nx, ny - depth), (nx + 0.8, ny)],
                    dxfattribs={"layer": "CRANS"},
                )
            for measurement in piece["measurements"]:
                start = (measurement["start"][0] + x_offset, measurement["start"][1] + y_offset)
                end = (measurement["end"][0] + x_offset, measurement["end"][1] + y_offset)
                msp.add_line(start, end, dxfattribs={"layer": "MESURES"})
            lx, ly = piece["labelPoint"][0] + x_offset, piece["labelPoint"][1] + y_offset
            msp.add_text(
                f"{piece['name']} {size}",
                dxfattribs={"layer": "ANNOTATION", "height": 3.2},
            ).set_placement((lx, ly), align=TextEntityAlignment.MIDDLE_CENTER)
            x_cursor = x_offset + box["max_x"] + 18
        y_cursor += max((piece["bbox"]["height"] for piece in pattern["pieces"]), default=90) + 26

    with NamedTemporaryFile(mode="w+b", delete=True, suffix=".dxf") as tmp:
        doc.saveas(tmp.name)
        tmp.seek(0)
        return tmp.read()
