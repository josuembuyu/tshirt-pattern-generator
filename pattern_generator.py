from __future__ import annotations

from backend.app.garments.tshirt import TShirtPatternGenerator
from backend.app.models import GarmentOptions, Measurements


class PatternGenerator:
    """Adaptateur de compatibilité pour les anciens scripts.

    Le nouveau code doit utiliser backend.app.garments.tshirt.TShirtPatternGenerator.
    """

    def __init__(self, measures: dict, options: dict | None = None):
        options = options or {}
        normalized_options = {
            "fit": "oversized" if options.get("fit") == "oversize" else options.get("fit", "regular"),
            "neckline": options.get("neckline", options.get("collar", "round")),
            "sleeve": options.get("sleeve", options.get("sleeve_type", "short")),
            "seam_allowance": options.get("seam_allowance", 1.0),
            "neckband_reduction": options.get("neckband_reduction", 0.86),
        }
        self.measures = Measurements(**measures)
        self.options = GarmentOptions(**normalized_options)
        self._payload = None

    def generate(self):
        self._payload = TShirtPatternGenerator(self.measures, self.options).generate().to_payload()
        return {
            piece["id"]: {
                "points": piece["stitchPoints"],
                "cut_points": piece["cutPoints"],
                "grainline": [piece["grainline"]["start"], piece["grainline"]["end"]],
                "notches": [notch["point"] for notch in piece["notches"]],
                "label": piece["name"],
            }
            for piece in self._payload["pieces"]
        }

    def get_bounds(self):
        if not self._payload:
            self.generate()
        return self._payload["bounds"]
