"use client";

import React, { useState, useRef } from "react";
import { Dialog, DialogBody, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";
import { api, StudentResponse } from "@/lib/api";
import {
  UploadCloud,
  X,
  AlertTriangle,
  ShieldCheck,
  FileImage,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadItem {
  id: string;
  file: File;
  previewUrl: string;
  studentId: string;
  studentName: string;
  error?: string;
}

interface WorksheetUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  assessmentId: string;
  assessmentTitle: string;
  existingCount?: number;
  onUploadSuccess: (newResponses: StudentResponse[]) => void;
}

export function WorksheetUploadModal({
  isOpen,
  onClose,
  assessmentId,
  assessmentTitle,
  existingCount = 0,
  onUploadSuccess,
}: WorksheetUploadModalProps) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const processFiles = (fileList: FileList | File[]) => {
    setGeneralError(null);
    const newItems: UploadItem[] = [];
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    const maxBytes = 10 * 1024 * 1024; // 10MB ceiling

    let currentIdx = existingCount + items.length + 1;

    Array.from(fileList).forEach((file) => {
      let error: string | undefined;
      if (!allowedTypes.includes(file.type) && !file.name.match(/\.(jpe?g|png|webp)$/i)) {
        error = "Unsupported format (must be JPG, PNG, or WebP)";
      } else if (file.size > maxBytes) {
        error = "File exceeds 10 MB ceiling";
      }

      const previewUrl = URL.createObjectURL(file);
      const formattedIdx = String(currentIdx).padStart(2, "0");
      newItems.push({
        id: `${file.name}_${Date.now()}_${Math.random()}`,
        file,
        previewUrl,
        studentId: `stu_${formattedIdx}`,
        studentName: `Student-${formattedIdx}`,
        error,
      });
      currentIdx++;
    });

    setItems((prev) => [...prev, ...newItems]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const handleRemoveItem = (id: string) => {
    setItems((prev) => {
      const target = prev.find((item) => item.id === id);
      if (target) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((item) => item.id !== id);
    });
  };

  const handleUpdateStudent = (id: string, field: "studentId" | "studentName", val: string) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, [field]: val } : item))
    );
  };

  const handleUpload = async () => {
    const validItems = items.filter((item) => !item.error);
    if (validItems.length === 0) {
      setGeneralError("Please select at least one valid image file.");
      return;
    }

    try {
      setUploading(true);
      setGeneralError(null);

      const files = validItems.map((item) => item.file);
      const mappings: Record<string, { student_id?: string; student_name?: string }> = {};
      validItems.forEach((item) => {
        mappings[item.file.name] = {
          student_id: item.studentId.trim(),
          student_name: item.studentName.trim(),
        };
      });

      const uploaded = await api.uploadWorksheetBatch(assessmentId, files, mappings);
      onUploadSuccess(uploaded);
      onClose();
    } catch (err: any) {
      console.error("Upload failed:", err);
      setGeneralError(err.message || "Failed to upload student worksheets.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      size="lg"
      title="Upload Handwritten Student Worksheets"
      description={`Add student worksheets to: ${assessmentTitle}`}
      noPadding
    >
      <div className="flex flex-col flex-1 min-h-0">
        <DialogBody className="space-y-4 sm:space-y-5 text-xs sm:text-sm">
          {generalError && (
            <Alert variant="error">
              <AlertTriangle className="w-4 h-4 mr-2 shrink-0" />
              <span>{generalError}</span>
            </Alert>
          )}

          {/* Intake Security & Offline Notice Strip */}
          <div className="p-3 sm:p-3.5 rounded-xl bg-surface-subtle border border-border-default space-y-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-xs sm:text-sm text-ink-primary">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Intake Security &amp; Privacy Verification</span>
            </div>
            <p className="text-[11px] sm:text-xs text-ink-muted leading-relaxed">
              Magic-byte verified, EXIF stripped, and fine pencil detail preserved. In offline mode, worksheets are stored securely without synthetic AI hallucinations.
            </p>
          </div>

          {/* Drag and Drop Upload Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "border-2 border-dashed rounded-2xl p-5 sm:p-7 text-center cursor-pointer transition-all duration-150",
              isDragging
                ? "border-brand-primary bg-brand-light/30 ring-2 ring-brand-primary/20"
                : "border-border-default hover:border-brand-primary/60 hover:bg-surface-subtle"
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={handleFileChange}
            />
            <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-full bg-brand-light text-brand-primary flex items-center justify-center mx-auto mb-2.5 shadow-2xs">
              <UploadCloud className="w-5 h-5 sm:w-6 sm:h-6" />
            </div>
            <p className="font-semibold text-ink-primary text-xs sm:text-sm">
              Drag &amp; drop worksheet photos, or click to browse
            </p>
            <p className="text-[11px] sm:text-xs text-ink-muted mt-1">
              Supports JPG, PNG, and WebP • Up to 10 MB per image
            </p>
          </div>

          {/* Selected Worksheets List with Student ID Mapping */}
          {items.length > 0 && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs font-semibold text-ink-secondary">
                <span>Selected Worksheets ({items.length})</span>
                <button
                  type="button"
                  onClick={() => setItems([])}
                  className="text-[11px] text-ink-muted hover:text-accent-coral transition-colors"
                >
                  Clear all
                </button>
              </div>

              <div className="max-h-60 overflow-y-auto space-y-2.5 pr-1">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className={cn(
                      "p-3 rounded-xl border flex flex-col sm:flex-row sm:items-center gap-3 transition-colors",
                      item.error
                        ? "border-accent-coral/30 bg-accent-coral/5"
                        : "border-border-default bg-surface-base"
                    )}
                  >
                    {/* Top row on mobile: Thumbnail + info + remove */}
                    <div className="flex items-center gap-3 min-w-0 sm:flex-1">
                      {/* Thumbnail Preview */}
                      <div className="w-12 h-12 rounded-lg bg-surface-subtle overflow-hidden border border-border-default shrink-0 flex items-center justify-center">
                        <img
                          src={item.previewUrl}
                          alt={item.file.name}
                          className="w-full h-full object-cover"
                        />
                      </div>

                      {/* File Name & Size */}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-ink-primary truncate text-xs sm:text-sm">
                          {item.file.name}
                        </p>
                        <span className="font-mono text-[10px] sm:text-[11px] text-ink-muted block mt-0.5">
                          {formatFileSize(item.file.size)}
                        </span>
                        {item.error && (
                          <p className="text-[11px] text-accent-coral font-medium mt-0.5">
                            {item.error}
                          </p>
                        )}
                      </div>

                      {/* Remove Button on mobile */}
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(item.id)}
                        className="p-1.5 rounded-lg text-ink-muted hover:text-accent-coral hover:bg-surface-subtle transition-colors shrink-0 sm:hidden"
                        title="Remove worksheet"
                        aria-label="Remove worksheet"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Metadata & Student Mapping */}
                    {!item.error && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:w-72 shrink-0">
                        <Input
                          value={item.studentId}
                          onChange={(e) =>
                            handleUpdateStudent(item.id, "studentId", e.target.value)
                          }
                          placeholder="Student ID (e.g. stu_01)"
                          className="h-8 text-[11px] sm:text-xs py-1 px-2.5 font-mono"
                        />
                        <Input
                          value={item.studentName}
                          onChange={(e) =>
                            handleUpdateStudent(item.id, "studentName", e.target.value)
                          }
                          placeholder="Student Name"
                          className="h-8 text-[11px] sm:text-xs py-1 px-2.5"
                        />
                      </div>
                    )}

                    {/* Remove Button on desktop */}
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(item.id)}
                      className="p-1.5 rounded-lg text-ink-muted hover:text-accent-coral hover:bg-surface-subtle transition-colors shrink-0 hidden sm:block"
                      title="Remove worksheet"
                      aria-label="Remove worksheet"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </DialogBody>

        {/* Action Buttons Sticky Footer */}
        <DialogFooter className="justify-between flex-wrap gap-2">
          <span className="text-[11px] sm:text-xs text-ink-muted">
            {items.filter((i) => !i.error).length} valid worksheet(s) ready
          </span>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={onClose}
              disabled={uploading}
              className="px-4 py-2"
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="coral"
              size="sm"
              onClick={handleUpload}
              disabled={uploading || items.filter((i) => !i.error).length === 0}
              className="px-4 py-2"
            >
              {uploading ? (
                <>
                  <Spinner size="sm" className="mr-1.5" />
                  Uploading...
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4 mr-1.5" />
                  Upload Worksheets
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </div>
    </Dialog>
  );
}
