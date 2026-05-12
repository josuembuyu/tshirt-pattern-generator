import type { Bounds, PatternData, PatternPiece } from "../types/pattern";

export interface PlacedPiece {
  pattern: PatternData;
  piece: PatternPiece;
  x: number;
  y: number;
  opacity: number;
}

export const PIECE_COLORS: Record<string, string> = {
  front: "var(--piece-front)",
  back: "var(--piece-back)",
  sleeve: "var(--piece-sleeve)",
  neckband: "var(--piece-neckband)"
};

export function layoutPatterns(patterns: PatternData[], overlay: boolean, activeSize: string): PlacedPiece[] {
  if (!patterns.length) return [];
  const active = patterns.find((pattern) => pattern.size === activeSize) ?? patterns[0];
  const baseOffsets = new Map<string, number>();
  let cursor = 0;
  for (const piece of active.pieces) {
    const x = cursor - piece.bbox.min_x;
    baseOffsets.set(piece.id, x);
    cursor = x + piece.bbox.max_x + 18;
  }

  const placed: PlacedPiece[] = [];
  patterns.forEach((pattern, patternIndex) => {
    let rowCursor = 0;
    const rowOffset = overlay ? 0 : patternIndex * 112;
    pattern.pieces.forEach((piece) => {
      const x = overlay ? (baseOffsets.get(piece.id) ?? 0) - piece.bbox.min_x : rowCursor - piece.bbox.min_x;
      const y = rowOffset - piece.bbox.min_y;
      rowCursor = x + piece.bbox.max_x + 18;
      placed.push({
        pattern,
        piece,
        x,
        y,
        opacity: overlay && pattern.size !== activeSize ? 0.36 : 1
      });
    });
  });
  return placed;
}

export function boundsForPlaced(placed: PlacedPiece[]): Bounds {
  if (!placed.length) {
    return { min_x: -20, min_y: -20, max_x: 180, max_y: 120, width: 200, height: 140 };
  }
  const minX = Math.min(...placed.map(({ piece, x }) => piece.bbox.min_x + x));
  const minY = Math.min(...placed.map(({ piece, y }) => piece.bbox.min_y + y));
  const maxX = Math.max(...placed.map(({ piece, x }) => piece.bbox.max_x + x));
  const maxY = Math.max(...placed.map(({ piece, y }) => piece.bbox.max_y + y));
  return {
    min_x: minX - 12,
    min_y: minY - 18,
    max_x: maxX + 16,
    max_y: maxY + 14,
    width: maxX - minX + 28,
    height: maxY - minY + 32
  };
}

export function offsetPathD(d: string, xOffset: number, yOffset: number) {
  const tokens = d.split(/\s+/);
  const out: string[] = [];
  for (let index = 0; index < tokens.length;) {
    const token = tokens[index];
    if (token === "M" || token === "L") {
      out.push(token, `${Number(tokens[index + 1]) + xOffset}`, `${Number(tokens[index + 2]) + yOffset}`);
      index += 3;
    } else if (token === "C") {
      out.push(
        "C",
        `${Number(tokens[index + 1]) + xOffset}`,
        `${Number(tokens[index + 2]) + yOffset}`,
        `${Number(tokens[index + 3]) + xOffset}`,
        `${Number(tokens[index + 4]) + yOffset}`,
        `${Number(tokens[index + 5]) + xOffset}`,
        `${Number(tokens[index + 6]) + yOffset}`
      );
      index += 7;
    } else {
      out.push(token);
      index += 1;
    }
  }
  return out.join(" ");
}

export function pointsAttr(points: [number, number][], x: number, y: number) {
  return points.map(([px, py]) => `${px + x},${py + y}`).join(" ");
}

export function formatNumber(value: number, precision = 1) {
  return new Intl.NumberFormat("en", {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision
  }).format(value);
}
