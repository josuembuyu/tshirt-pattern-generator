import { motion } from "framer-motion";
import { Palette, Ruler, Shirt, SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { SegmentedControl } from "../ui/SegmentedControl";
import { usePatternStore } from "../../store/usePatternStore";
import type { FitName, Measurements, NecklineName, SleeveName, TextileMotif } from "../../types/pattern";

const HEX_COLOR_PATTERN = /^#[0-9a-fA-F]{6}$/;

const MEASURE_LABELS: Record<keyof Measurements, string> = {
  chest: "Tour de poitrine",
  length: "Longueur corps",
  shoulder: "Carrure épaules",
  neck: "Tour d'encolure",
  sleeve_short: "Manche courte",
  sleeve_long: "Manche longue"
};

const MEASURE_LIMITS: Record<keyof Measurements, [number, number, number]> = {
  chest: [70, 150, 0.5],
  length: [45, 105, 0.5],
  shoulder: [30, 70, 0.5],
  neck: [28, 58, 0.5],
  sleeve_short: [10, 40, 0.5],
  sleeve_long: [40, 80, 0.5]
};

export function LeftPanel() {
  const sizeOrder = usePatternStore((state) => state.sizeOrder);
  const activeSize = usePatternStore((state) => state.activeSize);
  const selectedSizes = usePatternStore((state) => state.selectedSizes);
  const gradingTable = usePatternStore((state) => state.gradingTable);
  const options = usePatternStore((state) => state.options);
  const appearance = usePatternStore((state) => state.appearance);
  const setActiveSize = usePatternStore((state) => state.setActiveSize);
  const toggleSelectedSize = usePatternStore((state) => state.toggleSelectedSize);
  const updateMeasurement = usePatternStore((state) => state.updateMeasurement);
  const updateOption = usePatternStore((state) => state.updateOption);
  const updateAppearance = usePatternStore((state) => state.updateAppearance);
  const measures = gradingTable[activeSize];

  return (
    <motion.aside className="panel left-panel" initial={{ opacity: 0, x: -18 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}>
      <section className="panel-section">
        <div className="section-heading">
          <Ruler size={15} />
          <span>Tailles</span>
        </div>
        <div className="size-grid">
          {sizeOrder.map((size) => (
            <button
              key={size}
              className={`size-cell ${activeSize === size ? "is-active" : ""} ${selectedSizes.includes(size) ? "is-selected" : ""}`}
              type="button"
              onClick={() => setActiveSize(size)}
              onDoubleClick={() => toggleSelectedSize(size)}
            >
              <span>{size}</span>
              <i />
            </button>
          ))}
        </div>
      </section>

      <section className="panel-section">
        <div className="section-heading">
          <SlidersHorizontal size={15} />
          <span>Mesures</span>
          <strong>{activeSize}</strong>
        </div>
        {(Object.keys(MEASURE_LABELS) as (keyof Measurements)[]).map((key) => {
          const [min, max, step] = MEASURE_LIMITS[key];
          return (
            <label className="measure-control" key={key}>
              <span>
                {MEASURE_LABELS[key]}
                <output>{measures[key].toFixed(1)} cm</output>
              </span>
              <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={measures[key]}
                onChange={(event) => updateMeasurement(key, Number(event.target.value))}
              />
            </label>
          );
        })}
      </section>

      <section className="panel-section">
        <div className="section-heading">
          <Shirt size={15} />
          <span>Vêtement</span>
        </div>
        <ControlGroup label="Coupe">
          <SegmentedControl<FitName>
            value={options.fit}
            options={[
              { value: "fitted", label: "Ajustée" },
              { value: "regular", label: "Standard" },
              { value: "oversized", label: "Oversize" }
            ]}
            onChange={(value) => updateOption("fit", value)}
          />
        </ControlGroup>
        <ControlGroup label="Col">
          <SegmentedControl<NecklineName>
            value={options.neckline}
            options={[
              { value: "round", label: "Rond" },
              { value: "v", label: "Col V" }
            ]}
            onChange={(value) => updateOption("neckline", value)}
          />
        </ControlGroup>
        <ControlGroup label="Manche">
          <SegmentedControl<SleeveName>
            value={options.sleeve}
            options={[
              { value: "short", label: "Courte" },
              { value: "long", label: "Longue" }
            ]}
            onChange={(value) => updateOption("sleeve", value)}
          />
        </ControlGroup>
        <label className="measure-control compact">
          <span>
            Marge de couture
            <output>{options.seam_allowance.toFixed(1)} cm</output>
          </span>
          <input
            type="range"
            min={0}
            max={3}
            step={0.1}
            value={options.seam_allowance}
            onChange={(event) => updateOption("seam_allowance", Number(event.target.value))}
          />
        </label>
      </section>

      <section className="panel-section">
        <div className="section-heading">
          <Palette size={15} />
          <span>Matière & motif</span>
        </div>

        <div className="color-pair">
          <ColorField label="Couleur tissu" value={appearance.base_color} onChange={(value) => updateAppearance("base_color", value)} />
          <ColorField label="Couleur motif" value={appearance.accent_color} onChange={(value) => updateAppearance("accent_color", value)} />
        </div>

        <ControlGroup label="Type">
          <SegmentedControl<TextileMotif>
            value={appearance.motif}
            options={[
              { value: "none", label: "Uni" },
              { value: "stripes", label: "Rayures" },
              { value: "checks", label: "Carreaux" },
              { value: "dots", label: "Pois" },
              { value: "rib", label: "Côte" },
              { value: "heather", label: "Chiné" }
            ]}
            onChange={(value) => updateAppearance("motif", value)}
          />
        </ControlGroup>

        <label className="measure-control compact">
          <span>
            Échelle motif
            <output>{appearance.scale.toFixed(1)} cm</output>
          </span>
          <input
            type="range"
            min={2}
            max={24}
            step={0.5}
            value={appearance.scale}
            onChange={(event) => updateAppearance("scale", Number(event.target.value))}
          />
        </label>

        <label className="measure-control compact">
          <span>
            Orientation
            <output>{appearance.angle.toFixed(0)}°</output>
          </span>
          <input
            type="range"
            min={-90}
            max={90}
            step={5}
            value={appearance.angle}
            onChange={(event) => updateAppearance("angle", Number(event.target.value))}
          />
        </label>

        <label className="measure-control compact">
          <span>
            Intensité
            <output>{Math.round(appearance.opacity * 100)}%</output>
          </span>
          <input
            type="range"
            min={0.1}
            max={0.85}
            step={0.05}
            value={appearance.opacity}
            onChange={(event) => updateAppearance("opacity", Number(event.target.value))}
          />
        </label>

        <div
          className={`textile-swatch motif-${appearance.motif}`}
          style={{
            "--fabric": appearance.base_color,
            "--motif": appearance.accent_color,
            "--motif-opacity": appearance.opacity,
            "--motif-scale": `${appearance.scale}px`,
            "--motif-angle": `${appearance.angle}deg`
          } as CSSProperties}
        />
      </section>
    </motion.aside>
  );
}

function ControlGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="control-group">
      <span>{label}</span>
      {children}
    </div>
  );
}

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  const [draft, setDraft] = useState(value.toUpperCase());

  useEffect(() => {
    setDraft(value.toUpperCase());
  }, [value]);

  const commit = (next: string) => {
    const normalized = next.trim();
    setDraft(normalized.toUpperCase());
    if (HEX_COLOR_PATTERN.test(normalized)) {
      onChange(normalized);
    }
  };

  return (
    <label className="color-control">
      <span>{label}</span>
      <div className="color-input-row">
        <input
          aria-label={`${label} sélecteur`}
          type="color"
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
        <input
          aria-label={`${label} hexadécimal`}
          className="color-hex-input"
          spellCheck={false}
          value={draft}
          onBlur={() => commit(draft)}
          onChange={(event) => {
            const next = event.target.value.slice(0, 7);
            setDraft(next.toUpperCase());
            if (HEX_COLOR_PATTERN.test(next)) {
              onChange(next);
            }
          }}
        />
      </div>
    </label>
  );
}
