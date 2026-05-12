from __future__ import annotations

from dataclasses import dataclass

from backend.app.engine.geometry import BezierPath, Point, cubic_point, distance, polyline_length, pt
from backend.app.engine.pattern import Grainline, MeasurementAnnotation, Notch, PatternPiece, PatternSet
from backend.app.engine.validation import compare_lengths, validate_piece_geometry
from backend.app.models import GarmentOptions, Measurements


@dataclass
class BlockMetrics:
    body_half_width: float
    hem_half_width: float
    body_length: float
    shoulder_half: float
    neck_width: float
    front_neck_depth: float
    back_neck_depth: float
    shoulder_drop: float
    armhole_depth: float
    sleeve_length: float
    sleeve_hem_half: float
    bicep_half: float


class TShirtPatternGenerator:
    garment = "tshirt"

    def __init__(self, measures: Measurements, options: GarmentOptions, size: str = "M"):
        self.measures = measures
        self.options = options
        self.size = size
        self.metrics = self._metrics()

    def generate(self) -> PatternSet:
        front, front_meta = self._build_body("front")
        back, back_meta = self._build_body("back")
        sleeve = self._build_sleeve(front_meta["armhole_length"], back_meta["armhole_length"])
        neckband = self._build_neckband(front_meta["neckline_length"], back_meta["neckline_length"])

        pieces = [front, back, sleeve, neckband]
        validations = []
        for piece in pieces:
            validations.extend(validate_piece_geometry(piece))

        validations.append(
            compare_lengths(
                "seam.side",
                "Couture côté devant/dos",
                front_meta["side_seam_length"],
                back_meta["side_seam_length"],
                0.35,
                "devant/dos",
            )
        )
        validations.append(
            compare_lengths(
                "seam.shoulder",
                "Couture épaule devant/dos",
                front_meta["shoulder_length"],
                back_meta["shoulder_length"],
                0.25,
                "devant/dos",
            )
        )
        validations.append(
            compare_lengths(
                "seam.armhole_sleeve_cap",
                "Tête de manche vs emmanchure",
                sleeve.metadata["cap_length"],
                front_meta["armhole_length"] + back_meta["armhole_length"],
                0.8,
                "manche",
            )
        )
        validations.append(
            compare_lengths(
                "neckband.length",
                "Bord-côte selon réduction",
                neckband.metadata["finished_length"],
                neckband.metadata["neckline_total"] * self.options.neckband_reduction,
                0.25,
                "bord-côte",
            )
        )

        return PatternSet(
            size=self.size,
            pieces=pieces,
            validations=validations,
            metadata={
                "garment": self.garment,
                "fit": self.options.fit,
                "neckline": self.options.neckline,
                "sleeve": self.options.sleeve,
                "seamAllowance": self.options.seam_allowance,
                "unit": "cm",
            },
        )

    def _metrics(self) -> BlockMetrics:
        fit = self.options.fit
        chest_ease = {"fitted": 4.0, "regular": 8.0, "oversized": 18.0}[fit]
        shoulder_add = {"fitted": -1.0, "regular": 0.5, "oversized": 5.0}[fit]
        armhole_add = {"fitted": -1.0, "regular": 0.0, "oversized": 3.2}[fit]
        length_add = {"fitted": -1.0, "regular": 0.0, "oversized": 3.0}[fit]

        body_half_width = (self.measures.chest + chest_ease) / 4
        hem_half_width = body_half_width + {"fitted": -1.4, "regular": 0.6, "oversized": 2.2}[fit]
        body_length = self.measures.length + length_add
        shoulder_half = self.measures.shoulder / 2 + shoulder_add / 2
        neck_width = self.measures.neck / 5.7
        front_neck_depth = self.measures.neck / (3.25 if self.options.neckline == "v" else 4.85)
        back_neck_depth = self.measures.neck / 12
        shoulder_drop = {"fitted": 2.8, "regular": 3.6, "oversized": 5.1}[fit]
        armhole_depth = self.measures.chest / 6 + 6.4 + armhole_add
        sleeve_length = self.measures.sleeve_long if self.options.sleeve == "long" else self.measures.sleeve_short
        bicep_half = self.measures.chest / 5.6 + {"fitted": 0.7, "regular": 1.8, "oversized": 4.4}[fit]
        sleeve_hem_half = (
            bicep_half * (0.68 if self.options.sleeve == "short" else 0.48)
            + {"fitted": -0.4, "regular": 0.0, "oversized": 1.2}[fit]
        )
        return BlockMetrics(
            body_half_width=body_half_width,
            hem_half_width=hem_half_width,
            body_length=body_length,
            shoulder_half=shoulder_half,
            neck_width=neck_width,
            front_neck_depth=front_neck_depth,
            back_neck_depth=back_neck_depth,
            shoulder_drop=shoulder_drop,
            armhole_depth=armhole_depth,
            sleeve_length=sleeve_length,
            sleeve_hem_half=sleeve_hem_half,
            bicep_half=bicep_half,
        )

    def _build_body(self, kind: str) -> tuple[PatternPiece, dict[str, float]]:
        m = self.metrics
        is_front = kind == "front"
        neck_depth = m.front_neck_depth if is_front else m.back_neck_depth
        right_neck = pt(m.neck_width, 0)
        left_neck = pt(-m.neck_width, 0)
        right_shoulder = pt(m.shoulder_half, m.shoulder_drop)
        left_shoulder = pt(-m.shoulder_half, m.shoulder_drop)
        right_underarm = pt(m.body_half_width, m.shoulder_drop + m.armhole_depth)
        left_underarm = pt(-m.body_half_width, m.shoulder_drop + m.armhole_depth)
        right_hem = pt(m.hem_half_width, m.body_length)
        left_hem = pt(-m.hem_half_width, m.body_length)
        center_neck = pt(0, neck_depth)

        path = BezierPath().move_to(center_neck)
        if is_front and self.options.neckline == "v":
            path.line_to(right_neck)
        else:
            path.cubic_to(pt(m.neck_width * 0.22, neck_depth), pt(m.neck_width, neck_depth * 0.35), right_neck)
        path.line_to(right_shoulder)

        front_bias = 1.0 if is_front else -0.7
        path.cubic_to(
            pt(m.shoulder_half + 0.5, m.shoulder_drop + m.armhole_depth * 0.34),
            pt(m.body_half_width - (3.3 + front_bias), m.shoulder_drop + m.armhole_depth * 0.86),
            right_underarm,
        )
        path.line_to(right_hem)
        path.line_to(left_hem)
        path.line_to(left_underarm)
        path.cubic_to(
            pt(-(m.body_half_width - (3.3 + front_bias)), m.shoulder_drop + m.armhole_depth * 0.86),
            pt(-(m.shoulder_half + 0.5), m.shoulder_drop + m.armhole_depth * 0.34),
            left_shoulder,
        )
        path.line_to(left_neck)
        if is_front and self.options.neckline == "v":
            path.line_to(center_neck)
        else:
            path.cubic_to(pt(-m.neck_width, neck_depth * 0.35), pt(-m.neck_width * 0.22, neck_depth), center_neck)
        path.close()

        neckline_points = []
        if is_front and self.options.neckline == "v":
            neckline_length = distance(left_neck, center_neck) + distance(center_neck, right_neck)
        else:
            for side in [-1, 1]:
                p0 = center_neck
                p1 = pt(side * m.neck_width * 0.22, neck_depth)
                p2 = pt(side * m.neck_width, neck_depth * 0.35)
                p3 = pt(side * m.neck_width, 0)
                neckline_points.extend(cubic_point(p0, p1, p2, p3, i / 28) for i in range(29))
            neckline_length = polyline_length(neckline_points)

        armhole_points = [
            cubic_point(
                right_shoulder,
                pt(m.shoulder_half + 0.5, m.shoulder_drop + m.armhole_depth * 0.34),
                pt(m.body_half_width - (3.3 + front_bias), m.shoulder_drop + m.armhole_depth * 0.86),
                right_underarm,
                i / 40,
            )
            for i in range(41)
        ]
        armhole_length = polyline_length(armhole_points)
        side_length = distance(right_underarm, right_hem)
        shoulder_length = distance(right_neck, right_shoulder)

        label = "DEVANT" if is_front else "DOS"
        grain_x = 0
        piece = PatternPiece(
            id=kind,
            name=label,
            size=self.size,
            stitch_path=path,
            label_point=pt(0, m.body_length * 0.48),
            grainline=Grainline(pt(grain_x, neck_depth + 8), pt(grain_x, m.body_length - 8), "MD" if is_front else "MDOS"),
            notches=[
                Notch(f"{kind}-shoulder-r", right_shoulder, 92, "single", "épaule"),
                Notch(f"{kind}-shoulder-l", left_shoulder, 88, "single", "épaule"),
                Notch(f"{kind}-underarm-r", right_underarm, 0, "single", "emmanchure"),
                Notch(f"{kind}-underarm-l", left_underarm, 180, "single", "emmanchure"),
            ],
            measurements=[
                MeasurementAnnotation(f"{kind}-chest", "1/2 poitrine", pt(-m.body_half_width, right_underarm[1] + 3), pt(m.body_half_width, right_underarm[1] + 3), m.body_half_width * 2),
                MeasurementAnnotation(f"{kind}-length", "longueur corps", pt(m.hem_half_width + 4, 0), pt(m.hem_half_width + 4, m.body_length), m.body_length),
            ],
            seam_allowance=self.options.seam_allowance,
            metadata={
                "neckline_length": round(neckline_length, 3),
                "armhole_length": round(armhole_length, 3),
                "side_seam_length": round(side_length, 3),
                "shoulder_length": round(shoulder_length, 3),
            },
        ).finalize()

        return piece, piece.metadata

    def _build_sleeve(self, front_armhole: float, back_armhole: float) -> PatternPiece:
        m = self.metrics
        target_cap = (front_armhole + back_armhole) * 0.992
        cap_half = m.bicep_half
        cap_height = self._solve_cap_height(cap_half, target_cap)
        right_underarm = pt(cap_half, cap_height)
        left_underarm = pt(-cap_half, cap_height)
        right_hem = pt(m.sleeve_hem_half, m.sleeve_length)
        left_hem = pt(-m.sleeve_hem_half, m.sleeve_length)

        right_c1 = pt(cap_half * 0.44, 0.8)
        right_c2 = pt(cap_half * 1.02, cap_height * 0.56)
        left_c1 = pt(-cap_half * 1.02, cap_height * 0.56)
        left_c2 = pt(-cap_half * 0.44, 0.8)

        path = (
            BezierPath()
            .move_to(pt(0, 0))
            .cubic_to(right_c1, right_c2, right_underarm)
            .line_to(right_hem)
            .line_to(left_hem)
            .line_to(left_underarm)
            .cubic_to(left_c1, left_c2, pt(0, 0))
            .close()
        )
        right_cap_points = [cubic_point(pt(0, 0), right_c1, right_c2, right_underarm, i / 44) for i in range(45)]
        left_cap_points = [cubic_point(left_underarm, left_c1, left_c2, pt(0, 0), i / 44) for i in range(45)]
        cap_length = polyline_length(right_cap_points) + polyline_length(left_cap_points)

        front_notch = cubic_point(pt(0, 0), right_c1, right_c2, right_underarm, 0.58)
        back_notch = cubic_point(left_underarm, left_c1, left_c2, pt(0, 0), 0.42)
        piece = PatternPiece(
            id="sleeve",
            name="MANCHE",
            size=self.size,
            stitch_path=path,
            label_point=pt(0, m.sleeve_length * 0.52),
            grainline=Grainline(pt(0, cap_height + 4), pt(0, m.sleeve_length - 5), "DROIT-FIL"),
            notches=[
                Notch("sleeve-cap", pt(0, 0), 90, "double", "tête"),
                Notch("sleeve-front", front_notch, 35, "single", "devant"),
                Notch("sleeve-back", back_notch, 145, "double", "dos"),
                Notch("sleeve-underarm-r", right_underarm, 0, "single", "dessous bras"),
                Notch("sleeve-underarm-l", left_underarm, 180, "single", "dessous bras"),
            ],
            measurements=[
                MeasurementAnnotation("sleeve-length", "longueur manche", pt(cap_half + 4, cap_height), pt(cap_half + 4, m.sleeve_length), m.sleeve_length - cap_height),
                MeasurementAnnotation("sleeve-bicep", "tour de bras", left_underarm, right_underarm, cap_half * 2),
            ],
            seam_allowance=self.options.seam_allowance,
            metadata={"cap_length": round(cap_length, 3), "target_cap_length": round(target_cap, 3), "cap_height": round(cap_height, 3)},
        ).finalize()
        return piece

    def _solve_cap_height(self, cap_half: float, target_cap: float) -> float:
        low, high = 5.0, 22.0
        for _ in range(28):
            mid = (low + high) / 2
            length = self._cap_length_for(cap_half, mid)
            if length < target_cap:
                low = mid
            else:
                high = mid
        return round((low + high) / 2, 3)

    def _cap_length_for(self, cap_half: float, cap_height: float) -> float:
        right = [
            cubic_point(pt(0, 0), pt(cap_half * 0.44, 0.8), pt(cap_half * 1.02, cap_height * 0.56), pt(cap_half, cap_height), i / 44)
            for i in range(45)
        ]
        left = [
            cubic_point(pt(-cap_half, cap_height), pt(-cap_half * 1.02, cap_height * 0.56), pt(-cap_half * 0.44, 0.8), pt(0, 0), i / 44)
            for i in range(45)
        ]
        return polyline_length(right) + polyline_length(left)

    def _build_neckband(self, front_neckline: float, back_neckline: float) -> PatternPiece:
        total = front_neckline + back_neckline
        finished = total * self.options.neckband_reduction
        height = 4.2
        path = (
            BezierPath()
            .move_to(pt(-finished / 2, 0))
            .line_to(pt(finished / 2, 0))
            .line_to(pt(finished / 2, height))
            .line_to(pt(-finished / 2, height))
            .close()
        )
        piece = PatternPiece(
            id="neckband",
            name="BORD-CÔTE",
            size=self.size,
            stitch_path=path,
            label_point=pt(0, height / 2),
            grainline=Grainline(pt(-finished / 2 + 5, height / 2), pt(finished / 2 - 5, height / 2), "MAXI ÉLASTICITÉ"),
            notches=[
                Notch("neckband-cf", pt(0, 0), 90, "single", "MD"),
                Notch("neckband-cb", pt(0, height), 270, "double", "MDOS"),
                Notch("neckband-q1", pt(-finished / 4, 0), 90, "single", "quart"),
                Notch("neckband-q3", pt(finished / 4, 0), 90, "single", "quart"),
            ],
            measurements=[
                MeasurementAnnotation("neckband-length", "longueur finie", pt(-finished / 2, height + 2), pt(finished / 2, height + 2), finished),
                MeasurementAnnotation("neckband-height", "largeur pliée", pt(finished / 2 + 2, 0), pt(finished / 2 + 2, height), height),
            ],
            seam_allowance=self.options.seam_allowance,
            metadata={"neckline_total": round(total, 3), "finished_length": round(finished, 3), "reduction": self.options.neckband_reduction},
        ).finalize()
        return piece
