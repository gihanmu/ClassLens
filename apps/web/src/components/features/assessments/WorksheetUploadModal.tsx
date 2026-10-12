"use client";

import React, { useState, useRef } from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { api, StudentResponse } from "@/lib/api";
import {
  UploadCloud,
  FileImage,
  X,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldCheck,
  Plus,
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
      title="Upload Handwritten Student Worksheets"
      description={`Add student worksheets to: ${assessmentTitle}`}
    >
      <div className="space-y-4 text-xs">
        {generalError && (
          <Alert variant="error">
            <AlertTriangle className="w-4 h-4 mr-2" />
            {generalError}
          </Alert>
        )}

        {/* Security & Truthfulness Notice */}
        <div className="p-3 rounded-xl bg-surface-subtle border border-border-default space-y-1.5">
          <div className="flex items-center gap-1.5 font-semibold text-ink-primary">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Intake Security &amp; Privacy Verification</span>
          </div>
          <p className="text-[11px] text-ink-muted leading-relaxed">
            All files are scanned for magic-byte authenticity, EXIF privacy metadata is stripped, and fine pencil lines are preserved.
          </p>
          <div className="pt-1 flex items-start gap-1.5 text-[11px] text-amber-800 bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-600" />
            <span>
              <strong>Offline Mode Notice:</strong> Uploaded worksheets are securely stored and previewable. In offline mode, the system does not fabricate AI vision results—live visual interpretation requires authorized live mode.
            </span>
          </div>
        </div>

        {/* Drag and Drop Upload Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all",
            isDragging
              ? "border-brand-primary bg-brand-light/30 ring-2 ring-brand-primary/20"
              : "border-border-default hover:border-brand-primary/50 hover:bg-surface-subtle"
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
          <div className="w-12 h-12 rounded-full bg-brand-light text-brand-primary flex items-center justify-center mx-auto mb-2 shadow-2xs">
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="font-semibold text-ink-primary text-sm">
            Drag &amp; drop worksheet photos or click to browse
          </p>
          <p className="text-[11px] text-ink-muted mt-1">
            Supports JPG, JPEG, PNG, WebP • Maximum 10 MB per image
          </p>
        </div>

        {/* Selected Worksheets List with Student ID Mapping */}
        {items.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-ink-secondary">
              <span>Selected Worksheets ({items.length})</span>
              <button
                type="button"
                onClick={() => setItems([])}
                className="text-[11px] text-ink-muted hover:text-accent-coral"
              >
                Clear all
              </button>
            </div>

            <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
              {items.map((item) => (
                <div
                  key={item.id}
                  className={cn(
                    "p-2.5 rounded-xl border flex items-center gap-3 transition-colors",
                    item.error
                      ? "border-accent-coral/30 bg-accent-coral/5"
                      : "border-border-default bg-surface-base"
                  )}
                >
                  {/* Thumbnail Preview */}
                  <div className="w-12 h-12 rounded-lg bg-surface-subtle overflow-hidden border border-border-default shrink-0 flex items-center justify-center">
                    <img
                      src={item.previewUrl}
                      alt={item.file.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  {/* Metadata & Student Mapping */}
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium text-ink-primary truncate text-xs">
                        {item.file.name}
                      </p>
                      <span className="font-mono text-[10px] text-ink-muted shrink-0">
                        {formatFileSize(item.file.size)}
                      </span>
                    </div>

                    {item.error ? (
                      <p className="text-[11px] text-accent-coral font-medium">
                        {item.error}
                      </p>
                    ) : (
                      <div className="grid grid-cols-2 gap-2 pt-0.5">
                        <Input
                          value={item.studentId}
                          onChange={(e) =>
                            handleUpdateStudent(item.id, "studentId", e.target.value)
                          }
                          placeholder="Student ID"
                          className="h-7 text-[11px] py-1 px-2 font-mono"
                        />
                        <Input
                          value={item.studentName}
                          onChange={(e) =>
                            handleUpdateStudent(item.id, "studentName", e.target.value)
                          }
                          placeholder="Student Name"
                          className="h-7 text-[11px] py-1 px-2"
                        />
                      </div>
                    )}
                  </div>

                  {/* Remove Button */}
                  <button
                    type="button"
                    onClick={() => handleRemoveItem(item.id)}
                    className="p-1 rounded text-ink-muted hover:text-accent-coral hover:bg-surface-subtle"
                    title="Remove worksheet"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="pt-2 flex items-center justify-between border-t border-border-default">
          <span className="text-[11px] text-ink-muted">
            {items.filter((i) => !i.error).length} valid worksheet(s) ready
          </span>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={onClose}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="coral"
              size="sm"
              onClick={handleUpload}
              disabled={uploading || items.filter((i) => !i.error).length === 0}
            >
              {uploading ? (
                <>
                  <Spinner size="sm" className="mr-1.5" />
                  Uploading...
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
                  Upload Worksheets
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
