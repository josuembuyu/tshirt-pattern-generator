from __future__ import annotations

from pathlib import Path


APP_NAME = "AtelierCAD"
APP_VERSION = "2.0.0"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

DEFAULT_SIZE_CHART = {
    "XS": {"chest": 88, "length": 68, "shoulder": 40, "neck": 36, "sleeve_short": 20, "sleeve_long": 58},
    "S": {"chest": 92, "length": 70, "shoulder": 42, "neck": 37, "sleeve_short": 21, "sleeve_long": 59},
    "M": {"chest": 96, "length": 72, "shoulder": 44, "neck": 38, "sleeve_short": 22, "sleeve_long": 60},
    "L": {"chest": 100, "length": 74, "shoulder": 46, "neck": 39, "sleeve_short": 23, "sleeve_long": 61},
    "XL": {"chest": 104, "length": 76, "shoulder": 48, "neck": 40, "sleeve_short": 24, "sleeve_long": 62},
    "XXL": {"chest": 108, "length": 78, "shoulder": 50, "neck": 41, "sleeve_short": 25, "sleeve_long": 63},
}
