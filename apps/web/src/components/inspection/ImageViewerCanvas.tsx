"use client";

import React, { useState, useRef } from "react";
import { ZoomIn, ZoomOut, RotateCw, RefreshCw } from "lucide-react";

interface Observation {
  kind: string;
  value: string;
  confidence: number;
  start_pos?: number;
  end_pos?: number;
  direction?: string;
}

interface ImageViewerCanvasProps {
  responseId: string;
  observations?: Observation[];
}

export function ImageViewerCanvas({
  responseId,
  observations = [],
}: ImageViewerCanvasProps) {
  const [scale, setScale] = useState<number>(1.0);
  const [rotation, setRotation] = useState<number>(0);
  const [showOverlay, setShowOverlay] = useState<boolean>(true);
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const dragStart = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const handleZoomIn = () => setScale((s) => Math.min(3.0, +(s + 0.25).toFixed(2)));
  const handleZoomOut = () => setScale((s) => Math.max(0.5, +(s - 0.25).toFixed(2)));
  const handleRotate = () => setRotation((r) => (r + 90) % 360);
  const handleReset = () => {
    setScale(1.0);
    setRotation(0);
    setPosition({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    dragStart.current = { x: e.clientX - position.x, y: e.clientY - position.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const hops = observations.filter((o) => o.kind === "arrow_jump" || o.kind === "number_line_hop");

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-xl overflow-hidden border border-slate-700 shadow-inner">
      {/* Control Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700 text-slate-200">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Image Canvas
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-700 font-mono text-slate-300">
            {Math.round(scale * 100)}%
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            type="button"
            onClick={handleZoomIn}
            aria-label="Zoom in image"
            className="p-1.5 rounded hover:bg-slate-700 focus-visible:ring-2 focus-visible:ring-indigo-400 text-slate-300 hover:text-white transition-colors"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            aria-label="Zoom out image"
            className="p-1.5 rounded hover:bg-slate-700 focus-visible:ring-2 focus-visible:ring-indigo-400 text-slate-300 hover:text-white transition-colors"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={handleRotate}
            aria-label="Rotate image 90 degrees clockwise"
            className="p-1.5 rounded hover:bg-slate-700 focus-visible:ring-2 focus-visible:ring-indigo-400 text-slate-300 hover:text-white transition-colors"
          >
            <RotateCw className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={handleReset}
            aria-label="Reset zoom and position"
            className="p-1.5 rounded hover:bg-slate-700 focus-visible:ring-2 focus-visible:ring-indigo-400 text-slate-300 hover:text-white transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <div className="h-4 w-px bg-slate-700 mx-1" />
          <label className="flex items-center space-x-1 text-xs text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showOverlay}
              onChange={(e) => setShowOverlay(e.target.checked)}
              className="rounded bg-slate-700 border-slate-600 text-indigo-500 focus:ring-indigo-400"
            />
            <span>AI Marks Overlay</span>
          </label>
        </div>
      </div>

      {/* Interactive Viewport */}
      <div
        className="relative flex-1 overflow-hidden cursor-grab active:cursor-grabbing flex items-center justify-center p-4"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <div
          className="relative transition-transform duration-75 select-none"
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale}) rotate(${rotation}deg)`,
            transformOrigin: "center center",
          }}
        >
          {/* Handwritten Student Response Image */}
          <img
            src={`/api/v1/responses/${responseId}/image`}
            alt={`Handwritten student response for ${responseId}`}
            className="max-w-none max-h-[500px] rounded shadow-md border border-slate-700 pointer-events-none object-contain bg-white"
            onError={(e) => {
              // Graceful placeholder if static asset is missing
              const target = e.currentTarget;
              target.onerror = null;
              target.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400' fill='%231e293b'><rect width='600' height='400'/><text x='50%' y='50%' fill='%2394a3b8' font-family='sans-serif' font-size='18' text-anchor='middle'>Handwritten Image Canvas: Problem #1065658</text></svg>";
            }}
          />

          {/* SVG Hop Overlay */}
          {showOverlay && hops.length > 0 && (
            <div className="absolute inset-0 pointer-events-none">
              <svg className="w-full h-full" viewBox="0 0 600 400" preserveAspectRatio="none">
                {hops.map((hop, idx) => {
                  const isLeft = hop.direction === "left";
                  const strokeColor = isLeft ? "#f59e0b" : "#10b981";
                  const yBase = 220 + idx * 18;
                  return (
                    <g key={idx}>
                      <path
                        d={`M 150 ${yBase} Q 300 ${yBase - 50} 450 ${yBase}`}
                        fill="none"
                        stroke={strokeColor}
                        strokeWidth="3"
                        strokeDasharray="4 2"
                      />
                      <text
                        x={280}
                        y={yBase - 30}
                        fill={strokeColor}
                        fontSize="12"
                        fontWeight="bold"
                        className="bg-black/50"
                      >
                        {hop.value}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
