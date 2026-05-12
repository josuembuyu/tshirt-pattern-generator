from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


SizeName = Literal["XS", "S", "M", "L", "XL", "XXL"]
FitName = Literal["regular", "oversized", "fitted"]
NecklineName = Literal["round", "v"]
SleeveName = Literal["short", "long"]
TextileMotif = Literal["none", "stripes", "checks", "dots", "rib", "heather"]


class Measurements(BaseModel):
    chest: float = Field(..., ge=70, le=150)
    length: float = Field(..., ge=45, le=105)
    shoulder: float = Field(..., ge=30, le=70)
    neck: float = Field(..., ge=28, le=58)
    sleeve_short: float = Field(22, ge=10, le=40)
    sleeve_long: float = Field(60, ge=40, le=80)


class GarmentOptions(BaseModel):
    fit: FitName = "regular"
    neckline: NecklineName = "round"
    sleeve: SleeveName = "short"
    seam_allowance: float = Field(1.0, ge=0, le=3)
    neckband_reduction: float = Field(0.86, ge=0.72, le=0.98)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_names(cls, data):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "collar" in normalized and "neckline" not in normalized:
            normalized["neckline"] = normalized["collar"]
        if "sleeve_type" in normalized and "sleeve" not in normalized:
            normalized["sleeve"] = normalized["sleeve_type"]
        if normalized.get("fit") == "oversize":
            normalized["fit"] = "oversized"
        return normalized

    @field_validator("seam_allowance")
    @classmethod
    def round_allowance(cls, value: float) -> float:
        return round(value, 2)


class TextileAppearance(BaseModel):
    base_color: str = Field("#d8a454", pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str = Field("#1f6f68", pattern=r"^#[0-9a-fA-F]{6}$")
    motif: TextileMotif = "none"
    scale: float = Field(8, ge=2, le=24)
    angle: float = Field(0, ge=-90, le=90)
    opacity: float = Field(0.38, ge=0.1, le=0.85)


class PatternRequest(BaseModel):
    size: SizeName = "M"
    measures: Measurements
    options: GarmentOptions = Field(default_factory=GarmentOptions)
    appearance: TextileAppearance = Field(default_factory=TextileAppearance)
    selected_sizes: list[SizeName] = Field(default_factory=lambda: ["M"])
    grading_table: dict[SizeName, Measurements] | None = None


class ExportRequest(BaseModel):
    pattern: dict | None = None
    size: SizeName = "M"
    measures: Measurements
    options: GarmentOptions = Field(default_factory=GarmentOptions)
    appearance: TextileAppearance = Field(default_factory=TextileAppearance)
    selected_sizes: list[SizeName] = Field(default_factory=lambda: ["M"])
    grading_table: dict[SizeName, Measurements] | None = None


class ProjectFile(BaseModel):
    version: str = "2.0.0"
    name: str = "Base T-shirt"
    active_size: SizeName = "M"
    options: GarmentOptions = Field(default_factory=GarmentOptions)
    appearance: TextileAppearance = Field(default_factory=TextileAppearance)
    grading_table: dict[SizeName, Measurements]
    selected_sizes: list[SizeName] = Field(default_factory=lambda: ["M"])
