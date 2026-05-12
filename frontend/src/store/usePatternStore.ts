import { create } from "zustand";
import { downloadBlob, downloadProject, exportPattern, generatePatterns, getSizeChart } from "../lib/api";
import type {
  ExportFormat,
  GarmentOptions,
  Measurements,
  PatternResponse,
  ProjectFile,
  SizeName,
  TextileAppearance
} from "../types/pattern";

const SIZE_ORDER: SizeName[] = ["XS", "S", "M", "L", "XL", "XXL"];

const DEFAULT_CHART: Record<SizeName, Measurements> = {
  XS: { chest: 88, length: 68, shoulder: 40, neck: 36, sleeve_short: 20, sleeve_long: 58 },
  S: { chest: 92, length: 70, shoulder: 42, neck: 37, sleeve_short: 21, sleeve_long: 59 },
  M: { chest: 96, length: 72, shoulder: 44, neck: 38, sleeve_short: 22, sleeve_long: 60 },
  L: { chest: 100, length: 74, shoulder: 46, neck: 39, sleeve_short: 23, sleeve_long: 61 },
  XL: { chest: 104, length: 76, shoulder: 48, neck: 40, sleeve_short: 24, sleeve_long: 62 },
  XXL: { chest: 108, length: 78, shoulder: 50, neck: 41, sleeve_short: 25, sleeve_long: 63 }
};

const DEFAULT_OPTIONS: GarmentOptions = {
  fit: "regular",
  neckline: "round",
  sleeve: "short",
  seam_allowance: 1,
  neckband_reduction: 0.86
};

const DEFAULT_APPEARANCE: TextileAppearance = {
  base_color: "#d8a454",
  accent_color: "#1f6f68",
  motif: "none",
  scale: 8,
  angle: 0,
  opacity: 0.38
};

type LayerKey = "grid" | "rulers" | "textile" | "stitch" | "cut" | "grain" | "notches" | "labels" | "measurements";

const STORAGE_KEY = "ateliercad:tshirt:autosave:v2";
const DEFAULT_CAMERA = { zoom: 1, panX: 0, panY: 0 };
const DEFAULT_LAYERS: Record<LayerKey, boolean> = {
  grid: true,
  rulers: true,
  textile: true,
  stitch: true,
  cut: true,
  grain: true,
  notches: true,
  labels: true,
  measurements: true
};

interface Snapshot {
  activeSize: SizeName;
  options: GarmentOptions;
  appearance: TextileAppearance;
  gradingTable: Record<SizeName, Measurements>;
  selectedSizes: SizeName[];
}

interface PatternState {
  sizeOrder: SizeName[];
  activeSize: SizeName;
  selectedSizes: SizeName[];
  gradingTable: Record<SizeName, Measurements>;
  options: GarmentOptions;
  appearance: TextileAppearance;
  response: PatternResponse | null;
  isLoading: boolean;
  error: string | null;
  overlayMode: boolean;
  camera: { zoom: number; panX: number; panY: number };
  layers: Record<LayerKey, boolean>;
  history: Snapshot[];
  future: Snapshot[];
  init: () => Promise<void>;
  regenerate: () => Promise<void>;
  setActiveSize: (size: SizeName) => void;
  toggleSelectedSize: (size: SizeName) => void;
  updateMeasurement: (key: keyof Measurements, value: number, size?: SizeName) => void;
  updateOption: <K extends keyof GarmentOptions>(key: K, value: GarmentOptions[K]) => void;
  updateAppearance: <K extends keyof TextileAppearance>(key: K, value: TextileAppearance[K]) => void;
  toggleLayer: (layer: LayerKey) => void;
  setOverlayMode: (value: boolean) => void;
  setCamera: (camera: Partial<PatternState["camera"]>) => void;
  resetCamera: () => void;
  undo: () => void;
  redo: () => void;
  saveProject: () => void;
  loadProject: (project: ProjectFile) => void;
  exportFile: (format: ExportFormat) => Promise<void>;
}

interface AutosaveDraft {
  version: number;
  activeSize: SizeName;
  selectedSizes: SizeName[];
  gradingTable: Record<SizeName, Measurements>;
  options: GarmentOptions;
  appearance: TextileAppearance;
  overlayMode: boolean;
  camera: PatternState["camera"];
  layers: Record<LayerKey, boolean>;
}

export const usePatternStore = create<PatternState>((set, get) => ({
  sizeOrder: SIZE_ORDER,
  activeSize: "M",
  selectedSizes: ["M"],
  gradingTable: DEFAULT_CHART,
  options: DEFAULT_OPTIONS,
  appearance: DEFAULT_APPEARANCE,
  response: null,
  isLoading: false,
  error: null,
  overlayMode: false,
  camera: DEFAULT_CAMERA,
  layers: DEFAULT_LAYERS,
  history: [],
  future: [],
  init: async () => {
    const draft = readAutosave();
    let sizeOrder = SIZE_ORDER;
    let baseChart = DEFAULT_CHART;
    try {
      const data = await getSizeChart();
      sizeOrder = data.order;
      baseChart = data.chart;
    } catch {
      sizeOrder = SIZE_ORDER;
      baseChart = DEFAULT_CHART;
    }

    if (draft) {
      set({
        sizeOrder,
        activeSize: draft.activeSize,
        selectedSizes: draft.selectedSizes,
        gradingTable: mergeGradingTable(baseChart, draft.gradingTable),
        options: { ...DEFAULT_OPTIONS, ...draft.options },
        appearance: { ...DEFAULT_APPEARANCE, ...draft.appearance },
        overlayMode: draft.overlayMode,
        camera: { ...DEFAULT_CAMERA, ...draft.camera },
        layers: { ...DEFAULT_LAYERS, ...draft.layers }
      });
    } else {
      set({ sizeOrder, gradingTable: baseChart });
    }
    await get().regenerate();
  },
  regenerate: async () => {
    const state = get();
    set({ isLoading: true, error: null });
    try {
      const response = await generatePatterns({
        size: state.activeSize,
        measures: state.gradingTable[state.activeSize],
        options: state.options,
        appearance: state.appearance,
        selected_sizes: state.selectedSizes,
        grading_table: state.gradingTable
      });
      set({ response, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "La génération du patron a échoué", isLoading: false });
    }
  },
  setActiveSize: (size) => {
    commit(set, get);
    set((state) => ({
      activeSize: size,
      selectedSizes: state.selectedSizes.includes(size) ? state.selectedSizes : [size]
    }));
    writeAutosave(get());
  },
  toggleSelectedSize: (size) => {
    commit(set, get);
    set((state) => {
      const exists = state.selectedSizes.includes(size);
      const selectedSizes = exists ? state.selectedSizes.filter((item) => item !== size) : [...state.selectedSizes, size];
      return { selectedSizes: selectedSizes.length ? selectedSizes : [state.activeSize], overlayMode: selectedSizes.length > 1 ? state.overlayMode : false };
    });
    writeAutosave(get());
  },
  updateMeasurement: (key, value, size) => {
    commit(set, get);
    set((state) => {
      const target = size ?? state.activeSize;
      return {
        gradingTable: {
          ...state.gradingTable,
          [target]: { ...state.gradingTable[target], [key]: value }
        }
      };
    });
    writeAutosave(get());
  },
  updateOption: (key, value) => {
    commit(set, get);
    set((state) => ({ options: { ...state.options, [key]: value } }));
    writeAutosave(get());
  },
  updateAppearance: (key, value) => {
    commit(set, get);
    set((state) => ({ appearance: { ...state.appearance, [key]: value } }));
    writeAutosave(get());
  },
  toggleLayer: (layer) => {
    set((state) => ({ layers: { ...state.layers, [layer]: !state.layers[layer] } }));
    writeAutosave(get());
  },
  setOverlayMode: (overlayMode) => {
    set({ overlayMode });
    writeAutosave(get());
  },
  setCamera: (camera) => {
    set((state) => ({ camera: { ...state.camera, ...camera } }));
    writeAutosave(get());
  },
  resetCamera: () => {
    set({ camera: DEFAULT_CAMERA });
    writeAutosave(get());
  },
  undo: () => {
    const state = get();
    const previous = state.history[state.history.length - 1];
    if (!previous) return;
    const current = snapshot(state);
    set({
      ...previous,
      history: state.history.slice(0, -1),
      future: [current, ...state.future]
    });
    writeAutosave(get());
  },
  redo: () => {
    const state = get();
    const next = state.future[0];
    if (!next) return;
    const current = snapshot(state);
    set({
      ...next,
      history: [...state.history, current].slice(-40),
      future: state.future.slice(1)
    });
    writeAutosave(get());
  },
  saveProject: () => {
    const state = get();
    downloadProject({
      version: "2.0.0",
      name: "Base T-shirt",
      active_size: state.activeSize,
      options: state.options,
      appearance: state.appearance,
      grading_table: state.gradingTable,
      selected_sizes: state.selectedSizes
    });
  },
  loadProject: (project) => {
    set({
      activeSize: project.active_size,
      selectedSizes: project.selected_sizes,
      options: project.options,
      appearance: project.appearance ?? DEFAULT_APPEARANCE,
      gradingTable: project.grading_table,
      history: [],
      future: []
    });
    writeAutosave(get());
  },
  exportFile: async (format) => {
    const state = get();
    const blob = await exportPattern(format, {
      size: state.activeSize,
      measures: state.gradingTable[state.activeSize],
      options: state.options,
      appearance: state.appearance,
      selected_sizes: format === "zip" ? state.sizeOrder : state.selectedSizes,
      grading_table: state.gradingTable
    });
    const sizes = format === "zip" ? "gradation" : state.selectedSizes.join("-");
    downloadBlob(blob, `ateliercad_patron_tshirt_${sizes}.${format}`);
  }
}));

function snapshot(state: PatternState): Snapshot {
  return {
    activeSize: state.activeSize,
    options: structuredClone(state.options),
    appearance: structuredClone(state.appearance),
    gradingTable: structuredClone(state.gradingTable),
    selectedSizes: [...state.selectedSizes]
  };
}

function commit(set: (partial: any) => void, get: () => PatternState) {
  const state = get();
  set({ history: [...state.history, snapshot(state)].slice(-40), future: [] });
}

function readAutosave(): AutosaveDraft | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const draft = JSON.parse(raw) as Partial<AutosaveDraft>;
    const activeSize = isSizeName(draft.activeSize) ? draft.activeSize : "M";
    const selectedSizes = Array.isArray(draft.selectedSizes) ? draft.selectedSizes.filter(isSizeName) : [activeSize];

    return {
      version: 2,
      activeSize,
      selectedSizes: selectedSizes.length ? selectedSizes : [activeSize],
      gradingTable: mergeGradingTable(DEFAULT_CHART, draft.gradingTable),
      options: { ...DEFAULT_OPTIONS, ...draft.options },
      appearance: { ...DEFAULT_APPEARANCE, ...draft.appearance },
      overlayMode: Boolean(draft.overlayMode),
      camera: {
        zoom: validNumber(draft.camera?.zoom, DEFAULT_CAMERA.zoom),
        panX: validNumber(draft.camera?.panX, DEFAULT_CAMERA.panX),
        panY: validNumber(draft.camera?.panY, DEFAULT_CAMERA.panY)
      },
      layers: { ...DEFAULT_LAYERS, ...draft.layers }
    };
  } catch {
    return null;
  }
}

function writeAutosave(state: PatternState) {
  if (typeof window === "undefined") return;
  const draft: AutosaveDraft = {
    version: 2,
    activeSize: state.activeSize,
    selectedSizes: state.selectedSizes,
    gradingTable: state.gradingTable,
    options: state.options,
    appearance: state.appearance,
    overlayMode: state.overlayMode,
    camera: state.camera,
    layers: state.layers
  };
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
  } catch {
    // Le navigateur peut refuser localStorage en navigation privée stricte.
  }
}

function mergeGradingTable(
  base: Record<SizeName, Measurements>,
  draft?: Partial<Record<SizeName, Partial<Measurements>>>
): Record<SizeName, Measurements> {
  return SIZE_ORDER.reduce((table, size) => {
    table[size] = { ...base[size], ...(draft?.[size] ?? {}) };
    return table;
  }, {} as Record<SizeName, Measurements>);
}

function isSizeName(value: unknown): value is SizeName {
  return typeof value === "string" && SIZE_ORDER.includes(value as SizeName);
}

function validNumber(value: unknown, fallback: number) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}
