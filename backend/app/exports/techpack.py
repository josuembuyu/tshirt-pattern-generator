from __future__ import annotations

from datetime import datetime
from io import BytesIO


DEFAULT_APPEARANCE = {
    "base_color": "#d8a454",
    "accent_color": "#1f6f68",
    "motif": "none",
    "scale": 8,
    "angle": 0,
    "opacity": 0.38,
}

MOTIF_LABELS = {
    "none": "uni",
    "stripes": "rayures",
    "checks": "carreaux",
    "dots": "pois",
    "rib": "côte",
    "heather": "chiné",
}


def export_pdf_techpack(patterns: list[dict], project_name: str = "Base T-shirt", appearance: dict | None = None) -> bytes:
    textile = {**DEFAULT_APPEARANCE, **(appearance or {})}
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
    except Exception:
        return _minimal_pdf(patterns, project_name)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    for index, pattern in enumerate(patterns):
        if index:
            pdf.showPage()
        pdf.setFillColor(colors.HexColor("#171a1d"))
        pdf.rect(0, 0, width, height, fill=True, stroke=False)
        pdf.setFillColor(colors.HexColor("#f2eadf"))
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(1.6 * cm, height - 1.8 * cm, project_name)
        pdf.setFont("Helvetica", 9)
        pdf.setFillColor(colors.HexColor("#aeb7bf"))
        pdf.drawString(1.6 * cm, height - 2.35 * cm, f"Taille {pattern['size']} | Généré le {datetime.utcnow().date().isoformat()} | unité cm")

        y = height - 3.4 * cm
        pdf.setFillColor(colors.HexColor("#d8a454"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(1.6 * cm, y, "Pièces du patron")
        y -= 0.55 * cm
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.HexColor("#f2eadf"))
        for piece in pattern["pieces"]:
            pdf.drawString(
                1.6 * cm,
                y,
                f"{piece['name']} : surface {piece['areaCm2']:.1f} cm2, surface coupe {piece['cutAreaCm2']:.1f} cm2, périmètre {piece['perimeterCm']:.1f} cm",
            )
            y -= 0.42 * cm

        y -= 0.45 * cm
        pdf.setFillColor(colors.HexColor("#ef8f7a"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(1.6 * cm, y, "Matière et coloris")
        y -= 0.55 * cm
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.HexColor("#f2eadf"))
        pdf.drawString(
            1.6 * cm,
            y,
            f"Tissu {textile['base_color']} | Motif {MOTIF_LABELS.get(textile['motif'], textile['motif'])} {textile['accent_color']} | échelle {float(textile['scale']):.1f} cm | angle {float(textile['angle']):.0f}°",
        )
        y -= 0.78 * cm

        pdf.setFillColor(colors.HexColor("#76d8c4"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(1.6 * cm, y, "Contrôle qualité")
        y -= 0.55 * cm
        pdf.setFont("Helvetica", 8)
        for validation in pattern["validations"]:
            color = {"ok": "#89d185", "warning": "#f0b35a", "error": "#ff6f59"}.get(validation["severity"], "#f2eadf")
            severity = {"ok": "OK", "warning": "AVERTISSEMENT", "error": "ERREUR"}.get(validation["severity"], validation["severity"].upper())
            pdf.setFillColor(colors.HexColor(color))
            pdf.drawString(1.6 * cm, y, f"[{severity}] {validation['message']}")
            y -= 0.42 * cm

        pdf.setStrokeColor(colors.HexColor("#3a4149"))
        pdf.rect(1.6 * cm, 1.6 * cm, width - 3.2 * cm, 5.4 * cm, stroke=True, fill=False)
        pdf.setFillColor(colors.HexColor("#aeb7bf"))
        pdf.drawString(1.9 * cm, 6.45 * cm, "Calques CAD : DÉCOUPE, COUTURE, DROIT-FIL, CRANS, MESURES, ANNOTATION")
        pdf.drawString(1.9 * cm, 6.0 * cm, "La géométrie source utilise des courbes de Bézier cubiques et des polylignes de production échantillonnées.")

    pdf.save()
    return buffer.getvalue()


def _minimal_pdf(patterns: list[dict], project_name: str) -> bytes:
    lines = [project_name, "Dossier technique PDF AtelierCAD", ""]
    for pattern in patterns:
        lines.append(f"Taille {pattern['size']}")
        for validation in pattern["validations"]:
            severity = {"ok": "OK", "warning": "AVERTISSEMENT", "error": "ERREUR"}.get(validation["severity"], validation["severity"].upper())
            lines.append(f"- {severity}: {validation['message']}")
    text = "\\n".join(lines).replace("(", "[").replace(")", "]")
    stream = f"BT /F1 12 Tf 72 760 Td ({text}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj",
    ]
    body = "%PDF-1.4\n" + "\n".join(objects) + "\n"
    offsets = [0]
    pos = len("%PDF-1.4\n")
    for obj in objects:
        offsets.append(pos)
        pos += len(obj) + 1
    xref_start = len(body)
    xref = "xref\n0 6\n0000000000 65535 f \n" + "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    trailer = f"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF"
    return (body + xref + trailer).encode("utf-8")
