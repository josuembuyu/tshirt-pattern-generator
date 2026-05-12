import { motion } from "framer-motion";
import { Crosshair, Maximize2, ZoomIn, ZoomOut } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { boundsForPlaced, layoutPatterns, offsetPathD, PIECE_COLORS, pointsAttr } from "../../lib/geometry";
import { usePatternStore } from "../../store/usePatternStore";
import type { MeasurementAnnotation, PatternPiece } from "../../types/pattern";
import { IconButton } from "../ui/IconButton";

export function CADCanvas() {
  const response = usePatternStore((state) => state.response);
  const activeSize = usePatternStore((state) => state.activeSize);
  const overlayMode = usePatternStore((state) => state.overlayMode);
  const camera = usePatternStore((state) => state.camera);
  const layers = usePatternStore((state) => state.layers);
  const appearance = usePatternStore((state) => state.appearance);
  const setCamera = usePatternStore((state) => state.setCamera);
  const resetCamera = usePatternStore((state) => state.resetCamera);
  const isLoading = usePatternStore((state) => state.isLoading);
  const error = usePatternStore((state) => state.error);
  const svgRef = useRef<SVGSVGElement>(null);
  const [drag, setDrag] = useState<{ x: number; y: number; panX: number; panY: number } | null>(null);
  const [surfaceSize, setSurfaceSize] = useState({ width: 1, height: 1 });

  const placed = useMemo(
    () => layoutPatterns(response?.patterns ?? [], overlayMode, activeSize),
    [response, overlayMode, activeSize]
  );
  const bounds = useMemo(() => boundsForPlaced(placed), [placed]);
  const view = useMemo(() => {
    const rawWidth = bounds.width / camera.zoom;
    const rawHeight = bounds.height / camera.zoom;
    const surfaceAspect = surfaceSize.width / Math.max(surfaceSize.height, 1);
    const rawAspect = rawWidth / Math.max(rawHeight, 1);
    const viewWidth = rawAspect > surfaceAspect ? rawWidth : rawHeight * surfaceAspect;
    const viewHeight = rawAspect > surfaceAspect ? rawWidth / surfaceAspect : rawHeight;
    const centerX = (bounds.min_x + bounds.max_x) / 2 + camera.panX;
    const centerY = (bounds.min_y + bounds.max_y) / 2 + camera.panY;

    return {
      x: centerX - viewWidth / 2,
      y: centerY - viewHeight / 2,
      width: viewWidth,
      height: viewHeight
    };
  }, [bounds, camera.panX, camera.panY, camera.zoom, surfaceSize.height, surfaceSize.width]);
  const viewBox = `${view.x} ${view.y} ${view.width} ${view.height}`;
  const grid = useMemo(() => makeGrid(view.x, view.y, view.width, view.height), [view.x, view.y, view.width, view.height]);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;

    const updateSize = () => {
      const box = svg.getBoundingClientRect();
      setSurfaceSize({ width: Math.max(box.width, 1), height: Math.max(box.height, 1) });
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(svg);
    return () => observer.disconnect();
  }, []);

  const pointerToUnits = (dx: number, dy: number) => {
    const box = svgRef.current?.getBoundingClientRect();
    if (!box) return { x: 0, y: 0 };
    return { x: (dx / box.width) * view.width, y: (dy / box.height) * view.height };
  };

  return (
    <motion.main className="workspace" initial={{ opacity: 0, scale: 0.985 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}>
      <div className="canvas-toolbar">
        <div className="canvas-status">
          <Crosshair size={15} />
          <span>{response?.project.name ?? "Plan de travail patron"}</span>
          <strong>{camera.zoom.toFixed(2)}x</strong>
        </div>
        <div className="canvas-actions">
          <IconButton icon={<ZoomOut size={15} />} label="Zoom arrière" onClick={() => setCamera({ zoom: Math.max(0.35, camera.zoom - 0.15) })} />
          <IconButton icon={<ZoomIn size={15} />} label="Zoom avant" onClick={() => setCamera({ zoom: Math.min(4, camera.zoom + 0.15) })} />
          <IconButton icon={<Maximize2 size={15} />} label="Ajuster la vue" onClick={resetCamera} />
        </div>
      </div>

      <svg
        ref={svgRef}
        className="cad-surface"
        viewBox={viewBox}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Plan de travail du patron paramétrique de T-shirt"
        onWheel={(event) => {
          event.preventDefault();
          const next = event.deltaY > 0 ? camera.zoom * 0.92 : camera.zoom * 1.08;
          setCamera({ zoom: Math.min(4, Math.max(0.35, next)) });
        }}
        onPointerDown={(event) => {
          svgRef.current?.setPointerCapture(event.pointerId);
          setDrag({ x: event.clientX, y: event.clientY, panX: camera.panX, panY: camera.panY });
        }}
        onPointerMove={(event) => {
          if (!drag) return;
          const delta = pointerToUnits(event.clientX - drag.x, event.clientY - drag.y);
          setCamera({ panX: drag.panX - delta.x, panY: drag.panY - delta.y });
        }}
        onPointerUp={() => setDrag(null)}
        onPointerCancel={() => setDrag(null)}
      >
        <defs>
          <marker id="grain-arrow" markerWidth="5" markerHeight="5" refX="2.5" refY="2.5" orient="auto">
            <path d="M 0 0 L 5 2.5 L 0 5 z" fill="var(--grain)" />
          </marker>
          <filter id="piece-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0.8" stdDeviation="0.7" floodColor="#000000" floodOpacity="0.25" />
          </filter>
          <TextilePatternDef appearance={appearance} />
        </defs>

        <rect x={view.x} y={view.y} width={view.width} height={view.height} fill="var(--canvas)" />

        {layers.grid && (
          <g className="grid-layer">
            {grid.minorX.map((x) => <line key={`mx-${x}`} x1={x} y1={view.y} x2={x} y2={view.y + view.height} />)}
            {grid.minorY.map((y) => <line key={`my-${y}`} x1={view.x} y1={y} x2={view.x + view.width} y2={y} />)}
            {grid.majorX.map((x) => <line className="major" key={`jx-${x}`} x1={x} y1={view.y} x2={x} y2={view.y + view.height} />)}
            {grid.majorY.map((y) => <line className="major" key={`jy-${y}`} x1={view.x} y1={y} x2={view.x + view.width} y2={y} />)}
          </g>
        )}

        {layers.rulers && (
          <g className="ruler-layer">
            <rect x={view.x} y={view.y} width={view.width} height={5} />
            <rect x={view.x} y={view.y} width={8} height={view.height} />
            {grid.majorX.map((x) => (
              <g key={`rx-${x}`}>
                <line x1={x} y1={view.y} x2={x} y2={view.y + 5} />
                <text x={x + 0.7} y={view.y + 3.3}>{x.toFixed(0)}</text>
              </g>
            ))}
            {grid.majorY.map((y) => (
              <g key={`ry-${y}`}>
                <line x1={view.x} y1={y} x2={view.x + 8} y2={y} />
                <text x={view.x + 1} y={y - 0.8}>{y.toFixed(0)}</text>
              </g>
            ))}
          </g>
        )}

        <g className="piece-layer">
          {placed.map(({ pattern, piece, x, y, opacity }) => {
            const color = PIECE_COLORS[piece.id] ?? "var(--piece-front)";
            return (
              <g key={`${pattern.size}-${piece.id}`} style={{ opacity }}>
                {layers.textile && (
                  <polygon
                    className="fabric-fill"
                    points={pointsAttr(piece.cutPoints, x, y)}
                    fill={appearance.motif === "none" ? appearance.base_color : "url(#textile-pattern)"}
                    style={{ opacity: appearance.motif === "none" ? Math.max(0.18, appearance.opacity * 0.72) : 1 }}
                  />
                )}
                {layers.cut && <polyline className="cut-line" points={pointsAttr(piece.cutPoints, x, y)} />}
                {layers.stitch && (
                  <path
                    className="stitch-line"
                    d={offsetPathD(piece.stitchPath, x, y)}
                    style={{ stroke: color, color }}
                    filter="url(#piece-shadow)"
                  />
                )}
                {layers.grain && (
                  <g className={`grainline ${isCompactPiece(piece) ? "compact" : ""}`}>
                    <line
                      x1={piece.grainline.start[0] + x}
                      y1={piece.grainline.start[1] + y}
                      x2={piece.grainline.end[0] + x}
                      y2={piece.grainline.end[1] + y}
                      markerStart="url(#grain-arrow)"
                      markerEnd="url(#grain-arrow)"
                    />
                    <text
                      x={grainLabelPosition(piece, x, y).x}
                      y={grainLabelPosition(piece, x, y).y}
                      textAnchor={grainLabelPosition(piece, x, y).anchor}
                    >
                      {piece.grainline.label}
                    </text>
                  </g>
                )}
                {layers.measurements && piece.measurements.map((measure) => {
                  const sx = measure.start[0] + x;
                  const sy = measure.start[1] + y;
                  const ex = measure.end[0] + x;
                  const ey = measure.end[1] + y;
                  const label = measurementLabelPosition(piece, measure, sx, sy, ex, ey);
                  return (
                    <g className={`measurement ${label.compact ? "compact" : ""} ${label.vertical ? "vertical" : ""}`} key={measure.id}>
                      <line x1={sx} y1={sy} x2={ex} y2={ey} />
                      <text x={label.x} y={label.y}>{measure.value.toFixed(1)} cm</text>
                    </g>
                  );
                })}
                {layers.notches && piece.notches.map((notch) => {
                  const nx = notch.point[0] + x;
                  const ny = notch.point[1] + y;
                  const depth = notch.kind === "double" ? 2.5 : 1.7;
                  return (
                    <g className="notch" key={notch.id}>
                      <path d={`M ${nx - 0.9} ${ny} L ${nx} ${ny - depth} L ${nx + 0.9} ${ny}`} />
                      {notch.kind === "double" && <path d={`M ${nx - 1.8} ${ny} L ${nx - 0.9} ${ny - depth} L ${nx} ${ny}`} />}
                    </g>
                  );
                })}
                {layers.labels && (() => {
                  const label = pieceLabelPosition(piece, x, y);
                  return (
                    <g className={`piece-label ${label.compact ? "compact" : ""}`}>
                      <text x={label.x} y={label.y}>{label.compact ? `${piece.name} ${pattern.size}` : piece.name}</text>
                      {!label.compact && <text className="size-label" x={label.x} y={label.y + 4.4}>{pattern.size}</text>}
                    </g>
                  );
                })()}
              </g>
            );
          })}
        </g>
      </svg>

      {!response && !isLoading && !error && (
        <div className="canvas-empty-state">
          <strong>Aucun patron généré</strong>
          <span>Lancez l'API FastAPI sur http://localhost:8000 puis rechargez la page.</span>
        </div>
      )}

      {(isLoading || error) && (
        <div className={`canvas-toast ${error ? "error" : ""}`}>
          {error || "Recalcul du patron"}
        </div>
      )}
    </motion.main>
  );
}

function isCompactPiece(piece: Pick<PatternPiece, "id" | "bbox">) {
  return piece.id === "neckband" || piece.bbox.height <= 12;
}

function pieceLabelPosition(piece: PatternPiece, x: number, y: number) {
  if (isCompactPiece(piece)) {
    return {
      compact: true,
      x: (piece.bbox.min_x + piece.bbox.max_x) / 2 + x,
      y: piece.bbox.min_y + y - 3.2
    };
  }
  return {
    compact: false,
    x: piece.labelPoint[0] + x,
    y: piece.labelPoint[1] + y
  };
}

function grainLabelPosition(piece: PatternPiece, x: number, y: number) {
  const centerX = (piece.grainline.start[0] + piece.grainline.end[0]) / 2 + x;
  const centerY = (piece.grainline.start[1] + piece.grainline.end[1]) / 2 + y;
  if (isCompactPiece(piece)) {
    return { x: centerX, y: centerY + 0.85, anchor: "middle" as const };
  }
  return { x: centerX + 1.4, y: centerY, anchor: "start" as const };
}

function measurementLabelPosition(
  piece: PatternPiece,
  measure: MeasurementAnnotation,
  sx: number,
  sy: number,
  ex: number,
  ey: number
) {
  const compact = isCompactPiece(piece);
  const vertical = Math.abs(ex - sx) < 0.001;
  const horizontal = Math.abs(ey - sy) < 0.001;

  if (compact && horizontal) {
    return { compact, vertical: false, x: (sx + ex) / 2, y: sy + 3.2 };
  }
  if (compact && vertical) {
    return { compact, vertical: true, x: sx + 3.1, y: (sy + ey) / 2 + 0.85 };
  }
  if (measure.id.endsWith("length") && vertical) {
    return { compact, vertical: true, x: sx + 2.8, y: (sy + ey) / 2 };
  }
  return { compact, vertical: false, x: (sx + ex) / 2, y: (sy + ey) / 2 - 1.2 };
}

function TextilePatternDef({ appearance }: { appearance: { base_color: string; accent_color: string; motif: string; scale: number; angle: number; opacity: number } }) {
  const scale = Math.max(2, appearance.scale);
  const baseOpacity = Math.max(0.12, appearance.opacity * 0.35);
  const motifOpacity = Math.max(0.08, appearance.opacity);

  if (appearance.motif === "none") {
    return null;
  }

  return (
    <pattern
      id="textile-pattern"
      patternUnits="userSpaceOnUse"
      width={scale}
      height={scale}
      patternTransform={`rotate(${appearance.angle})`}
    >
      <rect width={scale} height={scale} fill={appearance.base_color} opacity={baseOpacity} />
      {appearance.motif === "stripes" && (
        <rect width={Math.max(0.7, scale * 0.28)} height={scale} fill={appearance.accent_color} opacity={motifOpacity} />
      )}
      {appearance.motif === "checks" && (
        <>
          <rect width={Math.max(0.7, scale * 0.22)} height={scale} fill={appearance.accent_color} opacity={motifOpacity} />
          <rect width={scale} height={Math.max(0.7, scale * 0.22)} fill={appearance.accent_color} opacity={motifOpacity * 0.82} />
        </>
      )}
      {appearance.motif === "dots" && (
        <circle cx={scale / 2} cy={scale / 2} r={Math.max(0.6, scale * 0.18)} fill={appearance.accent_color} opacity={motifOpacity} />
      )}
      {appearance.motif === "rib" && (
        <>
          <rect x={scale * 0.18} width={Math.max(0.35, scale * 0.08)} height={scale} fill={appearance.accent_color} opacity={motifOpacity} />
          <rect x={scale * 0.58} width={Math.max(0.35, scale * 0.05)} height={scale} fill={appearance.accent_color} opacity={motifOpacity * 0.55} />
        </>
      )}
      {appearance.motif === "heather" && (
        <>
          <path d={`M 0 ${scale * 0.25} L ${scale} 0`} stroke={appearance.accent_color} strokeWidth={Math.max(0.25, scale * 0.045)} opacity={motifOpacity * 0.55} />
          <path d={`M 0 ${scale * 0.8} L ${scale} ${scale * 0.2}`} stroke={appearance.accent_color} strokeWidth={Math.max(0.18, scale * 0.032)} opacity={motifOpacity * 0.34} />
          <path d={`M ${scale * 0.35} ${scale} L ${scale} ${scale * 0.5}`} stroke={appearance.accent_color} strokeWidth={Math.max(0.18, scale * 0.026)} opacity={motifOpacity * 0.42} />
        </>
      )}
    </pattern>
  );
}

function makeGrid(minX: number, minY: number, width: number, height: number) {
  const maxX = minX + width;
  const maxY = minY + height;
  return {
    minorX: makeTicks(minX, maxX, 5),
    minorY: makeTicks(minY, maxY, 5),
    majorX: makeTicks(minX, maxX, 20),
    majorY: makeTicks(minY, maxY, 20)
  };
}

function makeTicks(min: number, max: number, step: number) {
  const start = Math.floor(min / step) * step;
  const ticks: number[] = [];
  for (let value = start; value <= max + step; value += step) {
    ticks.push(Number(value.toFixed(4)));
  }
  return ticks;
}
