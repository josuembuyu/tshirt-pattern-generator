import { FileArchive, FileJson, FileText, Redo2, Save, Scissors, Undo2, Upload } from "lucide-react";
import { useRef } from "react";
import { IconButton } from "../ui/IconButton";
import { usePatternStore } from "../../store/usePatternStore";
import type { ProjectFile } from "../../types/pattern";

export function TopBar() {
  const inputRef = useRef<HTMLInputElement>(null);
  const saveProject = usePatternStore((state) => state.saveProject);
  const loadProject = usePatternStore((state) => state.loadProject);
  const exportFile = usePatternStore((state) => state.exportFile);
  const undo = usePatternStore((state) => state.undo);
  const redo = usePatternStore((state) => state.redo);
  const canUndo = usePatternStore((state) => state.history.length > 0);
  const canRedo = usePatternStore((state) => state.future.length > 0);
  const isLoading = usePatternStore((state) => state.isLoading);

  const readProject = async (file?: File) => {
    if (!file) return;
    const project = JSON.parse(await file.text()) as ProjectFile;
    loadProject(project);
  };

  return (
    <header className="topbar">
      <div className="brand-lockup">
        <div className="brand-mark"><Scissors size={18} /></div>
        <div>
          <strong>AtelierCAD</strong>
          <span>Base T-shirt</span>
        </div>
      </div>

      <div className="command-strip">
        <IconButton icon={<Undo2 size={16} />} label="Annuler" onClick={undo} disabled={!canUndo} />
        <IconButton icon={<Redo2 size={16} />} label="Rétablir" onClick={redo} disabled={!canRedo} />
        <span className="toolbar-rule" />
        <IconButton icon={<Save size={16} />} label="Enregistrer le projet JSON" onClick={saveProject} />
        <IconButton icon={<Upload size={16} />} label="Charger un projet JSON" onClick={() => inputRef.current?.click()} />
        <input
          ref={inputRef}
          hidden
          type="file"
          accept="application/json,.json"
          onChange={(event) => readProject(event.target.files?.[0])}
        />
      </div>

      <div className="export-strip">
        <IconButton icon={<FileJson size={16} />} label="Exporter en SVG" onClick={() => exportFile("svg")} disabled={isLoading} />
        <IconButton icon={<FileText size={16} />} label="Exporter le dossier technique PDF" onClick={() => exportFile("pdf")} disabled={isLoading} />
        <IconButton icon={<Scissors size={16} />} label="Exporter en DXF" onClick={() => exportFile("dxf")} disabled={isLoading} />
        <button className="zip-button" type="button" onClick={() => exportFile("zip")} disabled={isLoading}>
          <FileArchive size={16} />
          ZIP
        </button>
      </div>
    </header>
  );
}
