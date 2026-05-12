import type {
  ExportFormat,
  GarmentOptions,
  Measurements,
  PatternResponse,
  ProjectFile,
  SizeChartResponse,
  SizeName,
  TextileAppearance
} from "../types/pattern";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export async function getSizeChart(): Promise<SizeChartResponse> {
  return request("/api/sizes");
}

export async function generatePatterns(input: {
  size: SizeName;
  measures: Measurements;
  options: GarmentOptions;
  appearance: TextileAppearance;
  selected_sizes: SizeName[];
  grading_table: Record<SizeName, Measurements>;
}): Promise<PatternResponse> {
  return request("/api/patterns/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function exportPattern(format: ExportFormat, input: {
  size: SizeName;
  measures: Measurements;
  options: GarmentOptions;
  appearance: TextileAppearance;
  selected_sizes: SizeName[];
  grading_table: Record<SizeName, Measurements>;
}): Promise<Blob> {
  const response = await safeFetch(`${API_BASE}/api/exports/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.blob();
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function downloadProject(project: ProjectFile) {
  const blob = new Blob([JSON.stringify(project, null, 2)], { type: "application/json" });
  downloadBlob(blob, `ateliercad_projet_tshirt_${project.active_size}.json`);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await safeFetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

async function safeFetch(path: string, init?: RequestInit) {
  try {
    return await fetch(path, init);
  } catch {
    throw new Error("API FastAPI non joignable. Lancez le backend sur http://localhost:8000 puis rechargez la page.");
  }
}
