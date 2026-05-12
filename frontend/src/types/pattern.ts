export type SizeName = "XS" | "S" | "M" | "L" | "XL" | "XXL";
export type FitName = "regular" | "oversized" | "fitted";
export type NecklineName = "round" | "v";
export type SleeveName = "short" | "long";
export type ExportFormat = "dxf" | "svg" | "pdf" | "zip";
export type TextileMotif = "none" | "stripes" | "checks" | "dots" | "rib" | "heather";

export interface Measurements {
  chest: number;
  length: number;
  shoulder: number;
  neck: number;
  sleeve_short: number;
  sleeve_long: number;
}

export interface GarmentOptions {
  fit: FitName;
  neckline: NecklineName;
  sleeve: SleeveName;
  seam_allowance: number;
  neckband_reduction: number;
}

export interface TextileAppearance {
  base_color: string;
  accent_color: string;
  motif: TextileMotif;
  scale: number;
  angle: number;
  opacity: number;
}

export interface Bounds {
  min_x: number;
  min_y: number;
  max_x: number;
  max_y: number;
  width: number;
  height: number;
}

export interface Grainline {
  start: [number, number];
  end: [number, number];
  label: string;
}

export interface Notch {
  id: string;
  point: [number, number];
  angle: number;
  kind: "single" | "double" | string;
  label: string;
}

export interface MeasurementAnnotation {
  id: string;
  label: string;
  start: [number, number];
  end: [number, number];
  value: number;
  unit: string;
}

export interface PatternPiece {
  id: string;
  name: string;
  size: SizeName;
  stitchPath: string;
  stitchPoints: [number, number][];
  cutPoints: [number, number][];
  grainline: Grainline;
  notches: Notch[];
  measurements: MeasurementAnnotation[];
  labelPoint: [number, number];
  seamAllowance: number;
  areaCm2: number;
  cutAreaCm2: number;
  perimeterCm: number;
  bbox: Bounds;
  warnings: string[];
  metadata: Record<string, number | string>;
}

export interface ValidationIssue {
  code: string;
  severity: "ok" | "warning" | "error";
  message: string;
  piece?: string;
  delta?: number;
}

export interface PatternData {
  size: SizeName;
  pieces: PatternPiece[];
  validations: ValidationIssue[];
  metadata: Record<string, number | string>;
  bounds: Bounds;
}

export interface PatternResponse {
  project: {
    name: string;
    unit: string;
    version: string;
  };
  activeSize: SizeName;
  patterns: PatternData[];
  sizeOrder: SizeName[];
  appearance?: TextileAppearance;
}

export interface SizeChartResponse {
  order: SizeName[];
  chart: Record<SizeName, Measurements>;
}

export interface ProjectFile {
  version: string;
  name: string;
  active_size: SizeName;
  options: GarmentOptions;
  appearance: TextileAppearance;
  grading_table: Record<SizeName, Measurements>;
  selected_sizes: SizeName[];
}
