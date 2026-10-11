"use client";

import React, { useState } from "react";
import { Check, Edit3, EyeOff, Save, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";

interface TeacherReviewFormProps {
  responseId: string;
  initialReviewStatus?: string;
  initialOverrideTaxonomy?: string;
  initialNotes?: string;
  onReviewSubmitted?: (updatedStatus: string) => void;
}

const TAXONOMY_OPTIONS = [
  { id: "MISC-ARITH-OFF-BY-ONE", label: "MISC-ARITH-OFF-BY-ONE: Off-by-One Interval Miscount" },
  { id: "MISC-DIR-INV", label: "MISC-DIR-INV: Directional Vector Inversion" },
  { id: "MISC-MAG-COUNT", label: "MISC-MAG-COUNT: Magnitude Miscount on Number Line" },
  { id: "MISC-LINE-INTERVAL-MISLABEL", label: "MISC-LINE-INTERVAL-MISLABEL: Tick Mark Interval Misinterpretation" },
  { id: "MISC-SIGN-CONFUSION", label: "MISC-SIGN-CONFUSION: Signed Integer Confusion" },
];

export function TeacherReviewForm({
  responseId,
  initialReviewStatus = "unreviewed",
  initialOverrideTaxonomy = "",
  initialNotes = "",
  onReviewSubmitted,
}: TeacherReviewFormProps) {
  const [decision, setDecision] = useState<string>(
    initialReviewStatus !== "unreviewed" ? initialReviewStatus : "approved_as_is"
  );
  const [overrideTaxonomy, setOverrideTaxonomy] = useState<string>(
    initialOverrideTaxonomy || "MISC-ARITH-OFF-BY-ONE"
  );
  const [notes, setNotes] = useState<string>(initialNotes || "");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [currentStatus, setCurrentStatus] = useState<string>(initialReviewStatus);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccessMessage(null);

    try {
      const taxonomy = decision === "overridden" ? overrideTaxonomy : undefined;
      const res = await api.submitReview(responseId, decision, taxonomy, notes);
      setCurrentStatus(res.teacher_review_status);
      setSuccessMessage(
        decision === "approved_as_is"
          ? "AI Diagnosis Approved"
          : decision === "overridden"
          ? "Diagnosis Overridden & Logged to Audit Trail"
          : "Response Marked Unreadable"
      );
      if (onReviewSubmitted) {
        onReviewSubmitted(res.teacher_review_status);
      }
    } catch (err) {
      console.error("Failed to submit review:", err);
      alert("Error saving review decision. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="font-semibold text-slate-800 text-sm tracking-wide uppercase">
            Teacher Verification & Override
          </h3>
          <p className="text-xs text-slate-500">
            Unilateral educator authority. All actions are logged to the immutable audit trail.
          </p>
        </div>
        <div>
          <span
            className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full border ${
              currentStatus === "approved_as_is"
                ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                : currentStatus === "overridden"
                ? "bg-indigo-50 text-indigo-800 border-indigo-300"
                : currentStatus === "marked_unreadable"
                ? "bg-slate-100 text-slate-700 border-slate-300"
                : "bg-amber-50 text-amber-800 border-amber-300"
            }`}
          >
            Status: {currentStatus.replace(/_/g, " ").toUpperCase()}
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Action Choice Buttons */}
        <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Teacher review decision">
          <button
            type="button"
            onClick={() => setDecision("approved_as_is")}
            aria-pressed={decision === "approved_as_is"}
            className={`p-3 rounded-lg border text-left flex flex-col items-start transition-all ${
              decision === "approved_as_is"
                ? "bg-emerald-50 border-emerald-500 ring-2 ring-emerald-500 text-emerald-950 font-medium"
                : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700"
            }`}
          >
            <div className="flex items-center space-x-1.5 mb-1">
              <Check className="h-4 w-4 text-emerald-600" aria-hidden="true" />
              <span className="text-xs font-bold">Approve As-Is</span>
            </div>
            <span className="text-[11px] text-slate-500">
              Confirm AI diagnosis without changes
            </span>
          </button>

          <button
            type="button"
            onClick={() => setDecision("overridden")}
            aria-pressed={decision === "overridden"}
            className={`p-3 rounded-lg border text-left flex flex-col items-start transition-all ${
              decision === "overridden"
                ? "bg-indigo-50 border-indigo-500 ring-2 ring-indigo-500 text-indigo-950 font-medium"
                : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700"
            }`}
          >
            <div className="flex items-center space-x-1.5 mb-1">
              <Edit3 className="h-4 w-4 text-indigo-600" aria-hidden="true" />
              <span className="text-xs font-bold">Override</span>
            </div>
            <span className="text-[11px] text-slate-500">
              Correct diagnosis taxonomy
            </span>
          </button>

          <button
            type="button"
            onClick={() => setDecision("marked_unreadable")}
            aria-pressed={decision === "marked_unreadable"}
            className={`p-3 rounded-lg border text-left flex flex-col items-start transition-all ${
              decision === "marked_unreadable"
                ? "bg-slate-200 border-slate-600 ring-2 ring-slate-600 text-slate-900 font-medium"
                : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700"
            }`}
          >
            <div className="flex items-center space-x-1.5 mb-1">
              <EyeOff className="h-4 w-4 text-slate-600" aria-hidden="true" />
              <span className="text-xs font-bold">Unreadable</span>
            </div>
            <span className="text-[11px] text-slate-500">
              Corrupt or illegible work
            </span>
          </button>
        </div>

        {/* Override Taxonomy Dropdown */}
        {decision === "overridden" && (
          <div className="space-y-1.5 bg-indigo-50/50 p-3 rounded-lg border border-indigo-200">
            <label htmlFor="override-taxonomy" className="block text-xs font-semibold text-indigo-950">
              Corrected Misconception Taxonomy:
            </label>
            <select
              id="override-taxonomy"
              value={overrideTaxonomy}
              onChange={(e) => setOverrideTaxonomy(e.target.value)}
              className="w-full text-xs rounded border border-indigo-300 p-2 bg-white text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              {TAXONOMY_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Pedagogical Notes */}
        <div className="space-y-1">
          <label htmlFor="teacher-notes" className="block text-xs font-semibold text-slate-700">
            Pedagogical Notes (Optional):
          </label>
          <textarea
            id="teacher-notes"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add contextual observations (e.g., student started counting at boundary tick instead of interval)..."
            className="w-full text-xs rounded border border-slate-300 p-2.5 bg-white text-slate-900 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
        </div>

        {/* Submit Button & Confirmation */}
        <div className="flex items-center justify-between pt-2">
          {successMessage ? (
            <span className="inline-flex items-center text-xs font-medium text-emerald-700 space-x-1">
              <CheckCircle className="h-4 w-4 text-emerald-600" aria-hidden="true" />
              <span>{successMessage}</span>
            </span>
          ) : (
            <span className="text-xs text-slate-400">Review decision is immediately applied</span>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:opacity-50 transition-colors shadow-sm"
          >
            <Save className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{submitting ? "Saving..." : "Save Review Decision"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
