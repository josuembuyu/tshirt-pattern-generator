from __future__ import annotations

from backend.app.garments.tshirt import TShirtPatternGenerator
from backend.app.models import GarmentOptions, Measurements


class GarmentRegistry:
    def __init__(self) -> None:
        self._generators = {"tshirt": TShirtPatternGenerator}

    def generate(self, garment: str, measures: Measurements, options: GarmentOptions, size: str):
        if garment not in self._generators:
            available = ", ".join(sorted(self._generators))
            raise ValueError(f"Vêtement non pris en charge '{garment}'. Disponibles : {available}")
        return self._generators[garment](measures, options, size).generate()


registry = GarmentRegistry()
