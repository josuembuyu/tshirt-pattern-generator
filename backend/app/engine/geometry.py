from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Iterable, Literal

Point = tuple[float, float]
CommandType = Literal["M", "L", "C", "Z"]


def pt(x: float, y: float) -> Point:
    return (round(float(x), 4), round(float(y), 4))


def add(a: Point, b: Point) -> Point:
    return pt(a[0] + b[0], a[1] + b[1])


def mirror_x(p: Point) -> Point:
    return pt(-p[0], p[1])


def distance(a: Point, b: Point) -> float:
    return hypot(b[0] - a[0], b[1] - a[1])


def lerp(a: Point, b: Point, t: float) -> Point:
    return pt(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def cubic_point(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    mt = 1 - t
    return pt(
        mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
        mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1],
    )


def polyline_length(points: Iterable[Point]) -> float:
    pts = list(points)
    return sum(distance(a, b) for a, b in zip(pts, pts[1:]))


def polygon_area(points: Iterable[Point]) -> float:
    pts = list(points)
    if len(pts) < 3:
        return 0
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        total += a[0] * b[1] - b[0] * a[1]
    return abs(total / 2)


def bbox(points: Iterable[Point]) -> dict[str, float]:
    pts = list(points)
    if not pts:
        return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0, "width": 0, "height": 0}
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return {
        "min_x": round(min_x, 3),
        "min_y": round(min_y, 3),
        "max_x": round(max_x, 3),
        "max_y": round(max_y, 3),
        "width": round(max_x - min_x, 3),
        "height": round(max_y - min_y, 3),
    }


@dataclass(frozen=True)
class PathCommand:
    type: CommandType
    points: tuple[Point, ...] = field(default_factory=tuple)


@dataclass
class BezierPath:
    commands: list[PathCommand] = field(default_factory=list)

    def move_to(self, p: Point) -> "BezierPath":
        self.commands.append(PathCommand("M", (p,)))
        return self

    def line_to(self, p: Point) -> "BezierPath":
        self.commands.append(PathCommand("L", (p,)))
        return self

    def cubic_to(self, c1: Point, c2: Point, p: Point) -> "BezierPath":
        self.commands.append(PathCommand("C", (c1, c2, p)))
        return self

    def close(self) -> "BezierPath":
        self.commands.append(PathCommand("Z"))
        return self

    def current_point(self) -> Point:
        for command in reversed(self.commands):
            if command.points:
                return command.points[-1]
        return (0, 0)

    def to_svg_d(self, offset: Point = (0, 0)) -> str:
        parts: list[str] = []
        for command in self.commands:
            if command.type == "M":
                p = add(command.points[0], offset)
                parts.append(f"M {p[0]:.3f} {p[1]:.3f}")
            elif command.type == "L":
                p = add(command.points[0], offset)
                parts.append(f"L {p[0]:.3f} {p[1]:.3f}")
            elif command.type == "C":
                c1, c2, p = [add(value, offset) for value in command.points]
                parts.append(
                    f"C {c1[0]:.3f} {c1[1]:.3f} {c2[0]:.3f} {c2[1]:.3f} {p[0]:.3f} {p[1]:.3f}"
                )
            elif command.type == "Z":
                parts.append("Z")
        return " ".join(parts)

    def sample(self, curve_steps: int = 28, include_close: bool = True) -> list[Point]:
        sampled: list[Point] = []
        cursor: Point | None = None
        start: Point | None = None
        for command in self.commands:
            if command.type == "M":
                cursor = command.points[0]
                start = cursor
                sampled.append(cursor)
            elif command.type == "L" and cursor:
                cursor = command.points[0]
                sampled.append(cursor)
            elif command.type == "C" and cursor:
                c1, c2, end = command.points
                for index in range(1, curve_steps + 1):
                    sampled.append(cubic_point(cursor, c1, c2, end, index / curve_steps))
                cursor = end
            elif command.type == "Z" and cursor and start and include_close and sampled[-1] != start:
                sampled.append(start)
                cursor = start
        return sampled

    def length(self, curve_steps: int = 40) -> float:
        return polyline_length(self.sample(curve_steps=curve_steps, include_close=False))

    def bbox(self) -> dict[str, float]:
        return bbox(self.sample())


def transformed(points: Iterable[Point], offset: Point = (0, 0)) -> list[Point]:
    return [add(p, offset) for p in points]


def offset_closed_polygon(points: list[Point], amount: float) -> tuple[list[Point], str | None]:
    if amount <= 0:
        return points, None
    try:
        from shapely.geometry import Polygon
        from shapely.geometry.polygon import orient
    except Exception:
        return centroid_offset(points, amount), "Shapely est indisponible ; la marge de couture utilise un repli par centroïde."

    polygon = Polygon(points)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if polygon.is_empty:
        return points, "Impossible de décaler un polygone invalide."

    buffered = polygon.buffer(amount, join_style=2, mitre_limit=4.0)
    if buffered.geom_type == "MultiPolygon":
        buffered = max(buffered.geoms, key=lambda item: item.area)

    buffered = orient(buffered, sign=1.0)
    return [pt(x, y) for x, y in list(buffered.exterior.coords)], None


def centroid_offset(points: list[Point], amount: float) -> list[Point]:
    clean = points[:-1] if points and points[0] == points[-1] else points
    if not clean:
        return points
    cx = sum(p[0] for p in clean) / len(clean)
    cy = sum(p[1] for p in clean) / len(clean)
    expanded: list[Point] = []
    for x, y in clean:
        dx, dy = x - cx, y - cy
        mag = hypot(dx, dy) or 1
        expanded.append(pt(x + dx / mag * amount, y + dy / mag * amount))
    expanded.append(expanded[0])
    return expanded
