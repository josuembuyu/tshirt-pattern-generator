from __future__ import annotations

from .geometry import Point, distance, polygon_area, polyline_length
from .pattern import PatternPiece


def issue(code: str, severity: str, message: str, piece: str | None = None, delta: float | None = None) -> dict:
    payload = {"code": code, "severity": severity, "message": message}
    if piece:
        payload["piece"] = piece
    if delta is not None:
        payload["delta"] = round(delta, 3)
    return payload


def validate_piece_geometry(piece: PatternPiece) -> list[dict]:
    points = piece.stitch_path.sample()
    results: list[dict] = []
    if len(points) < 4:
        results.append(issue("geometry.too_few_points", "error", "La pièce contient moins de quatre points échantillonnés.", piece.id))
    if polygon_area(points) <= 0.1:
        results.append(issue("geometry.zero_area", "error", "La surface de la pièce n'est pas exploitable en production.", piece.id))
    try:
        from shapely.geometry import LineString, Polygon
    except Exception:
        return results

    line = LineString(points)
    polygon = Polygon(points)
    if not line.is_simple:
        results.append(issue("geometry.self_intersection", "error", "La ligne de couture s'auto-intersecte.", piece.id))
    if not polygon.is_valid:
        results.append(issue("geometry.invalid_polygon", "error", "Le contour fermé de la pièce est invalide.", piece.id))
    return results


def compare_lengths(
    code: str,
    label: str,
    first: float,
    second: float,
    tolerance: float,
    piece: str | None = None,
) -> dict:
    delta = abs(first - second)
    severity = "ok"
    if delta > tolerance * 2:
        severity = "error"
    elif delta > tolerance:
        severity = "warning"
    message = f"{label} : {first:.2f} cm contre {second:.2f} cm"
    return issue(code, severity, message, piece, delta)


def point_length(points: list[Point]) -> float:
    return sum(distance(a, b) for a, b in zip(points, points[1:]))
