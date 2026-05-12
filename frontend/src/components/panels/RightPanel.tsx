import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Layers3, ListChecks, Ruler, Table2 } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { usePatternStore } from "../../store/usePatternStore";
import type { Measurements } from "../../types/pattern";
import { formatNumber } from "../../lib/geometry";

type Tab = "validation" | "layers" | "grading";

const LAYER_LABELS = {
  grid: "Grille",
  rulers: "Règles",
  textile: "Matière",
  stitch: "Couture",
  cut: "Découpe",
  grain: "Droit-fil",
  notches: "Crans",
  labels: "Étiquettes",
  measurements: "Mesures"
} as const;

export function RightPanel() {
  const [tab, setTab] = useState<Tab>("validation");
  const response = usePatternStore((state) => state.response);
  const layers = usePatternStore((state) => state.layers);
  const toggleLayer = usePatternStore((state) => state.toggleLayer);
  const gradingTable = usePatternStore((state) => state.gradingTable);
  const sizeOrder = usePatternStore((state) => state.sizeOrder);
  const selectedSizes = usePatternStore((state) => state.selectedSizes);
  const toggleSelectedSize = usePatternStore((state) => state.toggleSelectedSize);
  const updateMeasurement = usePatternStore((state) => state.updateMeasurement);
  const overlayMode = usePatternStore((state) => state.overlayMode);
  const setOverlayMode = usePatternStore((state) => state.setOverlayMode);

  const validations = response?.patterns.flatMap((pattern) => pattern.validations.map((item) => ({ ...item, size: pattern.size }))) ?? [];
  const totals = response?.patterns.reduce(
    (acc, pattern) => {
      acc.area += pattern.pieces.reduce((sum, piece) => sum + piece.cutAreaCm2, 0);
      acc.pieces += pattern.pieces.length;
      return acc;
    },
    { area: 0, pieces: 0 }
  ) ?? { area: 0, pieces: 0 };

  return (
    <motion.aside className="panel right-panel" initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}>
      <div className="metrics-band">
        <Metric label="Pièces" value={totals.pieces.toString()} />
        <Metric label="Surface coupe" value={`${formatNumber(totals.area / 10000, 2)} m²`} />
      </div>

      <div className="tab-strip">
        <TabButton active={tab === "validation"} icon={<ListChecks size={14} />} label="Contrôle" onClick={() => setTab("validation")} />
        <TabButton active={tab === "layers"} icon={<Layers3 size={14} />} label="Calques" onClick={() => setTab("layers")} />
        <TabButton active={tab === "grading"} icon={<Table2 size={14} />} label="Gradation" onClick={() => setTab("grading")} />
      </div>

      {tab === "validation" && (
        <section className="panel-section">
          <div className="section-heading">
            <ListChecks size={15} />
            <span>Contrôle</span>
          </div>
          <div className="validation-list">
            {validations.map((issue) => (
              <div className={`validation-row ${issue.severity}`} key={`${issue.size}-${issue.code}-${issue.piece ?? ""}`}>
                {issue.severity === "ok" ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
                <div>
                  <strong>{issue.size} - {validationTitle(issue.code)}</strong>
                  <span>{issue.message}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {tab === "layers" && (
        <section className="panel-section">
          <div className="section-heading">
            <Layers3 size={15} />
            <span>Calques</span>
          </div>
          <div className="layer-list">
            {(Object.keys(LAYER_LABELS) as (keyof typeof LAYER_LABELS)[]).map((layer) => (
              <label className="layer-toggle" key={layer}>
                <span>{LAYER_LABELS[layer]}</span>
                <input type="checkbox" checked={layers[layer]} onChange={() => toggleLayer(layer)} />
              </label>
            ))}
          </div>
          <label className="layer-toggle overlay-toggle">
            <span>Superposer les tailles</span>
            <input type="checkbox" checked={overlayMode} onChange={(event) => setOverlayMode(event.target.checked)} disabled={selectedSizes.length < 2} />
          </label>
        </section>
      )}

      {tab === "grading" && (
        <section className="panel-section grading-section">
          <div className="section-heading">
            <Ruler size={15} />
            <span>Gradation</span>
          </div>
          <div className="grading-table">
            <div className="grading-head">
              <span>Taille</span>
              <span>Poitrine</span>
              <span>Longueur</span>
              <span>Épaule</span>
              <span>Col</span>
            </div>
            {sizeOrder.map((size) => (
              <div className="grading-row" key={size}>
                <label className="grade-size">
                  <input type="checkbox" checked={selectedSizes.includes(size)} onChange={() => toggleSelectedSize(size)} />
                  {size}
                </label>
                {(["chest", "length", "shoulder", "neck"] as (keyof Measurements)[]).map((key) => (
                  <input
                    key={key}
                    type="number"
                    step={0.5}
                    value={gradingTable[size][key]}
                    onChange={(event) => updateMeasurement(key, Number(event.target.value), size)}
                  />
                ))}
              </div>
            ))}
          </div>
        </section>
      )}
    </motion.aside>
  );
}

function TabButton({ active, icon, label, onClick }: { active: boolean; icon: ReactNode; label: string; onClick: () => void }) {
  return (
    <button className={active ? "is-active" : ""} type="button" onClick={onClick}>
      {icon}
      {label}
    </button>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function validationTitle(code: string) {
  const labels: Record<string, string> = {
    "seam.side": "coutures côté",
    "seam.shoulder": "coutures épaules",
    "seam.armhole_sleeve_cap": "tête de manche / emmanchure",
    "neckband.length": "longueur bord-côte",
    "geometry.too_few_points": "géométrie incomplète",
    "geometry.zero_area": "surface invalide",
    "geometry.self_intersection": "auto-intersection",
    "geometry.invalid_polygon": "contour invalide"
  };
  return labels[code] ?? code;
}
