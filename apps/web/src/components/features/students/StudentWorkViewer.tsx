import * as React from "react";
import { cn } from "@/lib/utils";
import { ZoomIn, ZoomOut, RotateCcw, Layers, ChevronDown, ChevronUp } from "lucide-react";
import { IconButton } from "@/components/ui/icon-button";
import { Button } from "@/components/ui/button";

export interface HopOverlayData {
  start: number;
  end: number;
  label: string;
  isCorrect: boolean;
}

export interface StudentWorkViewerProps {
  imageUrl: string;
  studentLabel?: string;
  hops?: HopOverlayData[];
  className?: string;
}

export function StudentWorkViewer({
  imageUrl,
  studentLabel = "Student Submission",
  hops = [],
  className,
}: StudentWorkViewerProps) {
  const [zoom, setZoom] = React.useState(1);
  const [showOverlay, setShowOverlay] = React.useState(true);
  const [rotation, setRotation] = React.useState(0);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.75));
  const handleReset = () => {
    setZoom(1);
    setRotation(0);
  };

  return (
    <div
      className={cn(
        "relative flex flex-col rounded-xl bg-surface-base border border-border-default overflow-hidden shadow-xs h-full min-h-[460px]",
        className
      )}
    >
      {/* Top Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border-default bg-surface-subtle/80 backdrop-blur-xs z-10 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold text-ink-primary">
            {studentLabel}
          </span>
          <span className="text-[11px] text-ink-muted">
            • {Math.round(zoom * 100)}%
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {hops.length > 0 && (
            <Button
              variant={showOverlay ? "primary" : "outline"}
              size="sm"
              onClick={() => setShowOverlay(!showOverlay)}
              className="text-xs h-[36px] min-h-[36px] px-2.5"
            >
              <Layers className="w-3.5 h-3.5" aria-hidden="true" />
              {showOverlay ? "Hide Hops" : "Show Hops"}
            </Button>
          )}

          <div className="h-4 w-px bg-border-default mx-1" />

          <IconButton
            icon={<ZoomOut className="w-4 h-4" />}
            aria-label="Zoom out"
            size="sm"
            onClick={handleZoomOut}
            disabled={zoom <= 0.75}
          />
          <IconButton
            icon={<ZoomIn className="w-4 h-4" />}
            aria-label="Zoom in"
            size="sm"
            onClick={handleZoomIn}
            disabled={zoom >= 3}
          />
          <IconButton
            icon={<RotateCcw className="w-4 h-4" />}
            aria-label="Reset zoom and view"
            size="sm"
            onClick={handleReset}
          />
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="relative flex-1 bg-surface-muted/30 overflow-auto flex items-center justify-center p-4 select-none">
        <div
          className="relative transition-transform duration-150 ease-out flex items-center justify-center"
          style={{
            transform: `scale(${zoom}) rotate(${rotation}deg)`,
            transformOrigin: "center center",
          }}
        >
          <img
            src={imageUrl}
            alt={`Handwritten student math response for ${studentLabel}`}
            className="max-h-[600px] w-auto object-contain rounded-lg shadow-sm border border-border-default bg-white"
            draggable={false}
          />
        </div>

        {/* Floating Anchored Hops Bar (Outside scaled image wrapper) */}
        {showOverlay && hops.length > 0 && (
          <div className="absolute inset-x-4 bottom-4 pointer-events-none z-10 flex justify-center">
            <div className="pointer-events-auto bg-ink-primary/90 backdrop-blur-md text-white p-3 rounded-xl shadow-lg border border-white/20 max-w-md w-full">
              <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-white/10">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-accent-yellow flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-accent-yellow" />
                  Detected Number-Line Hops
                </span>
                <span className="text-[10px] font-mono text-white/70">
                  {hops.filter((h) => h.isCorrect).length}/{hops.length} Valid
                </span>
              </div>
              <div className="space-y-1 text-xs font-mono">
                {hops.map((hop, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      "flex items-center justify-between px-2 py-0.5 rounded",
                      hop.isCorrect
                        ? "bg-emerald-500/25 text-emerald-200"
                        : "bg-red-500/25 text-red-200"
                    )}
                  >
                    <span>Hop {idx + 1}: {hop.label}</span>
                    <span>[{hop.start} &rarr; {hop.end}]</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
