import { useEffect, useRef, useState } from "react";
import { CADCanvas } from "./components/cad/CADCanvas";
import { LeftPanel } from "./components/panels/LeftPanel";
import { RightPanel } from "./components/panels/RightPanel";
import { TopBar } from "./components/panels/TopBar";
import { usePatternStore } from "./store/usePatternStore";

export default function App() {
  const [ready, setReady] = useState(false);
  const init = usePatternStore((state) => state.init);
  const regenerate = usePatternStore((state) => state.regenerate);
  const saveProject = usePatternStore((state) => state.saveProject);
  const undo = usePatternStore((state) => state.undo);
  const redo = usePatternStore((state) => state.redo);
  const activeSize = usePatternStore((state) => state.activeSize);
  const selectedSizes = usePatternStore((state) => state.selectedSizes);
  const gradingTable = usePatternStore((state) => state.gradingTable);
  const options = usePatternStore((state) => state.options);
  const booted = useRef(false);

  useEffect(() => {
    init().finally(() => {
      booted.current = true;
      setReady(true);
    });
  }, [init]);

  useEffect(() => {
    if (!ready || !booted.current) return;
    const id = window.setTimeout(() => regenerate(), 120);
    return () => window.clearTimeout(id);
  }, [ready, regenerate, activeSize, selectedSizes, gradingTable, options]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const mod = event.metaKey || event.ctrlKey;
      if (!mod) return;
      if (event.key.toLowerCase() === "s") {
        event.preventDefault();
        saveProject();
      }
      if (event.key.toLowerCase() === "z" && !event.shiftKey) {
        event.preventDefault();
        undo();
      }
      if (event.key.toLowerCase() === "y" || (event.key.toLowerCase() === "z" && event.shiftKey)) {
        event.preventDefault();
        redo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [saveProject, undo, redo]);

  return (
    <div className="app-shell">
      <TopBar />
      <div className="cad-layout">
        <LeftPanel />
        <CADCanvas />
        <RightPanel />
      </div>
    </div>
  );
}
