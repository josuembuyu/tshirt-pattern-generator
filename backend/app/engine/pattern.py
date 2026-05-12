from __future__ import annotations

from dataclasses import dataclass, field

from .geometry import BezierPath, Point, bbox, offset_closed_polygon, polygon_area, polyline_length


@dataclass
class Notch:
    id: str
    point: Point
    angle: float = 0
    kind: str = "single"
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "point": [self.point[0], self.point[1]],
            "angle": self.angle,
            "kind": self.kind,
            "label": self.label,
        }


@dataclass
class Grainline:
    start: Point
    end: Point
    label: str = "GRAIN"

    def to_dict(self) -> dict:
        return {
            "start": [self.start[0], self.start[1]],
            "end": [self.end[0], self.end[1]],
            "label": self.label,
        }


@dataclass
class MeasurementAnnotation:
    id: str
    label: str
    start: Point
    end: Point
    value: float
    unit: str = "cm"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "start": [self.start[0], self.start[1]],
            "end": [self.end[0], self.end[1]],
            "value": round(self.value, 2),
            "unit": self.unit,
        }


@dataclass
class PatternPiece:
    id: str
    name: str
    size: str
    stitch_path: BezierPath
    label_point: Point
    grainline: Grainline
    notches: list[Notch] = field(default_factory=list)
    measurements: list[MeasurementAnnotation] = field(default_factory=list)
    seam_allowance: float = 1.0
    cut_path: list[Point] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, float | str] = field(default_factory=dict)

    def finalize(self) -> "PatternPiece":
        stitch_points = self.stitch_path.sample()
        self.cut_path, seam_warning = offset_closed_polygon(stitch_points, self.seam_allowance)
        if seam_warning:
            self.warnings.append(seam_warning)
        return self

    def to_payload(self) -> dict:
        stitch_points = self.stitch_path.sample()
        cut_points = self.cut_path or stitch_points
        all_points = stitch_points + cut_points
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "stitchPath": self.stitch_path.to_svg_d(),
            "stitchPoints": [[x, y] for x, y in stitch_points],
            "cutPoints": [[x, y] for x, y in cut_points],
            "grainline": self.grainline.to_dict(),
            "notches": [notch.to_dict() for notch in self.notches],
            "measurements": [measurement.to_dict() for measurement in self.measurements],
            "labelPoint": [self.label_point[0], self.label_point[1]],
            "seamAllowance": self.seam_allowance,
            "areaCm2": round(polygon_area(stitch_points), 2),
            "cutAreaCm2": round(polygon_area(cut_points), 2),
            "perimeterCm": round(polyline_length(stitch_points), 2),
            "bbox": bbox(all_points),
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass
class PatternSet:
    size: str
    pieces: list[PatternPiece]
    validations: list[dict]
    metadata: dict

    def to_payload(self) -> dict:
        points = []
        for piece in self.pieces:
            points.extend(piece.stitch_path.sample())
            points.extend(piece.cut_path)
        return {
            "size": self.size,
            "pieces": [piece.to_payload() for piece in self.pieces],
            "validations": self.validations,
            "metadata": self.metadata,
            "bounds": bbox(points),
        }
