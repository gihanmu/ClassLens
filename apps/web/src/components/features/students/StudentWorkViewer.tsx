import * as React from "react";
import { cn } from "@/lib/utils";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize2,
  Layers,
  AlertTriangle,
  ImageOff,
} from "lucide-react";
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
  isUnreadable?: boolean;
  evidenceSufficiency?: string;
}

export function StudentWorkViewer({
  imageUrl,
  studentLabel = "Student Submission",
  hops = [],
  className,
  isUnreadable = false,
  evidenceSufficiency,
}: StudentWorkViewerProps) {
  const [zoom, setZoom] = React.useState(1);
  const [pan, setPan] = React.useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = React.useState(false);
  const [dragStart, setDragStart] = React.useState({ x: 0, y: 0 });
  const [showOverlay, setShowOverlay] = React.useState(true);
  const [rotation, setRotation] = React.useState(0);
  const [imageError, setImageError] = React.useState(false);

  const containerRef = React.useRef<HTMLDivElement>(null);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.75));

  const handleFitToScreen = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setRotation(0);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Left mouse click only
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);
  const handleMouseLeave = () => setIsDragging(false);

  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      setIsDragging(true);
      setDragStart({
        x: e.touches[0].clientX - pan.x,
        y: e.touches[0].clientY - pan.y,
      });
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging || e.touches.length !== 1) return;
    setPan({
      x: e.touches[0].clientX - dragStart.x,
      y: e.touches[0].clientY - dragStart.y,
    });
  };

  const handleTouchEnd = () => setIsDragging(false);

  const isDegraded = isUnreadable || evidenceSufficiency === "insufficient";

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
            icon={<Maximize2 className="w-4 h-4" />}
            aria-label="Fit to screen"
            size="sm"
            onClick={handleFitToScreen}
          />
          <IconButton
            icon={<RotateCcw className="w-4 h-4" />}
            aria-label="Reset zoom, pan, and rotation"
            size="sm"
            onClick={handleReset}
          />
        </div>
      </div>

      {/* Degraded / Insufficient Evidence Banner */}
      {isDegraded && (
        <div className="bg-amber-500/10 border-b border-amber-300/60 px-4 py-2 flex items-center justify-between text-xs text-amber-900 z-10">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span className="font-medium">
              Degraded or Ambiguous Handwriting: Evidence is faint or partially obscured. Manual teacher review advised.
            </span>
          </div>
        </div>
      )}

      {/* Main Canvas Area with Drag/Pan */}
      <div
        ref={containerRef}
        className={cn(
          "relative flex-1 bg-surface-muted/30 overflow-hidden flex items-center justify-center p-4 select-none",
          zoom > 1 ? (isDragging ? "cursor-grabbing" : "cursor-grab") : "cursor-default"
        )}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {imageError ? (
          <div className="flex flex-col items-center justify-center text-center p-8 text-ink-muted">
            <ImageOff className="w-10 h-10 mb-2 opacity-50 text-ink-muted" />
            <p className="text-sm font-semibold">Handwritten Image Unavailable</p>
            <p className="text-xs mt-1">Could not load the original worksheet artifact.</p>
          </div>
        ) : (
          <div
            className="relative transition-transform duration-75 ease-out flex items-center justify-center pointer-events-none"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom}) rotate(${rotation}deg)`,
              transformOrigin: "center center",
            }}
          >
            <img
              src={imageUrl}
              alt={`Handwritten student math response for ${studentLabel}`}
              className="max-h-[600px] w-auto object-contain rounded-lg shadow-sm border border-border-default bg-white pointer-events-auto"
              draggable={false}
              onError={() => setImageError(true)}
            />
          </div>
        )}

        {/* Floating Anchored Hops Bar (Outside scaled image wrapper) */}
        {showOverlay && hops.length > 0 && !imageError && (
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
