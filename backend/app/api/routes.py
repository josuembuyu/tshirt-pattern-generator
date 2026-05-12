from __future__ import annotations

import io
import json
import zipfile
from copy import deepcopy

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse

from backend.app.core.config import APP_NAME, APP_VERSION, DEFAULT_SIZE_CHART, SIZE_ORDER
from backend.app.exports.dxf import export_dxf
from backend.app.exports.svg import export_svg, export_svg_bundle
from backend.app.exports.techpack import export_pdf_techpack
from backend.app.garments.registry import registry
from backend.app.models import ExportRequest, Measurements, PatternRequest, ProjectFile

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"name": APP_NAME, "version": APP_VERSION, "status": "ok"}


@router.get("/sizes")
def sizes() -> dict:
    return {"order": SIZE_ORDER, "chart": DEFAULT_SIZE_CHART}


@router.get("/size_chart")
def legacy_size_chart() -> dict:
    return DEFAULT_SIZE_CHART


@router.post("/patterns/generate")
def generate_patterns(request: PatternRequest) -> dict:
    selected = request.selected_sizes or [request.size]
    grading_table = request.grading_table or _default_grading_with_override(request.size, request.measures)
    patterns = []
    for size in selected:
        measures = grading_table.get(size) or Measurements(**DEFAULT_SIZE_CHART[size])
        pattern = registry.generate("tshirt", measures, request.options, size)
        patterns.append(pattern.to_payload())
    return {
        "project": {"name": "Base T-shirt", "unit": "cm", "version": APP_VERSION},
        "activeSize": request.size,
        "patterns": patterns,
        "sizeOrder": SIZE_ORDER,
        "appearance": request.appearance.model_dump(mode="json"),
    }


@router.post("/generate_pattern")
def legacy_generate_pattern(request: PatternRequest) -> dict:
    pattern = registry.generate("tshirt", request.measures, request.options, request.size).to_payload()
    return {
        "pieces": {
            piece["id"]: {
                "points": piece["stitchPoints"],
                "cut_points": piece["cutPoints"],
                "grainline": [piece["grainline"]["start"], piece["grainline"]["end"]],
                "notches": [notch["point"] for notch in piece["notches"]],
                "label": piece["name"],
            }
            for piece in pattern["pieces"]
        },
        "bounds": pattern["bounds"],
        "validations": pattern["validations"],
    }


@router.post("/exports/dxf")
def export_pattern_dxf(request: ExportRequest) -> StreamingResponse:
    patterns = _patterns_from_export_request(request)
    content = export_dxf(patterns, appearance=request.appearance.model_dump(mode="json"))
    return _download(content, "application/dxf", _filename(request, "dxf"))


@router.post("/exports/svg")
def export_pattern_svg(request: ExportRequest) -> StreamingResponse:
    patterns = _patterns_from_export_request(request)
    svg = export_svg_bundle(patterns, request.appearance.model_dump(mode="json"))
    return _download(svg.encode("utf-8"), "image/svg+xml", _filename(request, "svg"))


@router.post("/exports/pdf")
def export_pattern_pdf(request: ExportRequest) -> StreamingResponse:
    patterns = _patterns_from_export_request(request)
    content = export_pdf_techpack(patterns, appearance=request.appearance.model_dump(mode="json"))
    return _download(content, "application/pdf", _filename(request, "pdf"))


@router.post("/exports/zip")
def export_pattern_zip(request: ExportRequest) -> StreamingResponse:
    patterns = _patterns_from_export_request(request)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("projet.json", json.dumps(_project_payload(request), indent=2))
        archive.writestr("dossier_technique.pdf", export_pdf_techpack(patterns, appearance=request.appearance.model_dump(mode="json")))
        archive.writestr("patrons.dxf", export_dxf(patterns, appearance=request.appearance.model_dump(mode="json")))
        for pattern in patterns:
            archive.writestr(f"svg/patron_tshirt_{pattern['size']}.svg", export_svg(pattern, request.appearance.model_dump(mode="json")))
            archive.writestr(f"json/patron_tshirt_{pattern['size']}.json", json.dumps(pattern, indent=2))
    buffer.seek(0)
    return _download(buffer.getvalue(), "application/zip", _filename(request, "zip"))


@router.post("/export_dxf")
def legacy_export_dxf(request: ExportRequest) -> StreamingResponse:
    return export_pattern_dxf(request)


@router.post("/export_svg")
def legacy_export_svg(request: ExportRequest) -> StreamingResponse:
    return export_pattern_svg(request)


@router.post("/export_all_sizes")
def legacy_export_all_sizes(request: ExportRequest) -> StreamingResponse:
    request.selected_sizes = SIZE_ORDER
    return export_pattern_zip(request)


@router.post("/projects/normalize")
def normalize_project(project: ProjectFile) -> dict:
    return project.model_dump(mode="json")


def _default_grading_with_override(active_size: str, measures: Measurements) -> dict[str, Measurements]:
    table = {size: Measurements(**values) for size, values in deepcopy(DEFAULT_SIZE_CHART).items()}
    table[active_size] = measures
    return table


def _patterns_from_export_request(request: ExportRequest) -> list[dict]:
    if request.pattern:
        if "patterns" in request.pattern:
            return request.pattern["patterns"]
        if "pieces" in request.pattern:
            return [request.pattern]
    selected = request.selected_sizes or [request.size]
    grading_table = request.grading_table or _default_grading_with_override(request.size, request.measures)
    patterns = []
    for size in selected:
        measures = grading_table.get(size) or Measurements(**DEFAULT_SIZE_CHART[size])
        patterns.append(registry.generate("tshirt", measures, request.options, size).to_payload())
    return patterns


def _project_payload(request: ExportRequest) -> dict:
    return {
        "version": APP_VERSION,
        "name": "Base T-shirt",
        "active_size": request.size,
        "options": request.options.model_dump(mode="json"),
        "appearance": request.appearance.model_dump(mode="json"),
        "selected_sizes": request.selected_sizes,
        "grading_table": {
            size: measures.model_dump(mode="json")
            for size, measures in (request.grading_table or _default_grading_with_override(request.size, request.measures)).items()
        },
    }


def _filename(request: ExportRequest, ext: str) -> str:
    options = request.options
    sizes = "gradation" if len(request.selected_sizes) > 1 else request.size
    fit = {"fitted": "ajustee", "regular": "standard", "oversized": "oversize"}[options.fit]
    neckline = {"round": "col_rond", "v": "col_v"}[options.neckline]
    sleeve = {"short": "manche_courte", "long": "manche_longue"}[options.sleeve]
    return f"ateliercad_patron_tshirt_{sizes}_{fit}_{neckline}_{sleeve}.{ext}"


def _download(content: bytes, media_type: str, filename: str) -> StreamingResponse:
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(io.BytesIO(content), media_type=media_type, headers=headers)
