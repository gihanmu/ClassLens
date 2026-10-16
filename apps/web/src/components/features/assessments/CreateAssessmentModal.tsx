"use client";

import React, { useState } from "react";
import { Dialog, DialogBody, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";
import { api, Assessment, CreateAssessmentInput } from "@/lib/api";
import { BookOpen, Sparkles, AlertCircle } from "lucide-react";

interface CreateAssessmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAssessmentCreated: (assessment: Assessment) => void;
}

export function CreateAssessmentModal({
  isOpen,
  onClose,
  onAssessmentCreated,
}: CreateAssessmentModalProps) {
  const [title, setTitle] = useState("Integers on Number Line: Checkpoint 2");
  const [topic, setTopic] = useState("Integer operations on number lines");
  const [gradeLevel, setGradeLevel] = useState("Secondary 1");
  const [classId, setClassId] = useState("cls_sec1_math");
  const [questionText, setQuestionText] = useState(
    "Use the number line to evaluate -6 + 12 - 4"
  );
  const [latexFormula, setLatexFormula] = useState("-6 + 12 - 4");
  const [expectedAnswer, setExpectedAnswer] = useState("2");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Please provide an assessment title.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const input: CreateAssessmentInput = {
        title: title.trim(),
        class_id: classId.trim(),
        math_topic: topic.trim(),
        grade_level: gradeLevel.trim(),
        question_text: questionText.trim(),
        latex_formula: latexFormula.trim(),
        expected_answer: expectedAnswer.trim(),
      };
      const created = await api.createAssessment(input);
      onAssessmentCreated(created);
      onClose();
    } catch (err: any) {
      console.error("Failed to create assessment:", err);
      setError(err.message || "Failed to create assessment.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      size="lg"
      title="Create New Mathematics Assessment"
      description="Configure a diagnostic checkpoint for student handwritten worksheets."
      noPadding
    >
      <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
        <DialogBody className="space-y-4 sm:space-y-5 text-xs sm:text-sm">
          {error && (
            <Alert variant="error">
              <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
              <span>{error}</span>
            </Alert>
          )}

          {/* Scope and Architecture Badge */}
          <div className="p-3 sm:p-3.5 rounded-xl bg-brand-light/40 border border-brand-primary/20 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-xs sm:text-sm text-brand-primary">
              <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-brand-primary shrink-0" />
              <span>Singapore Secondary 1 Math Scope</span>
            </div>
            <p className="text-[11px] sm:text-xs text-ink-secondary leading-relaxed">
              Specialized for <strong>integer operations on number lines</strong> with deterministic SymPy verification and misconception classification.
            </p>
          </div>

          {/* Assessment Title */}
          <div className="space-y-1.5">
            <label className="font-semibold text-ink-primary block text-xs sm:text-sm">
              Assessment Title <span className="text-accent-coral">*</span>
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Integers on Number Line: Checkpoint 2"
              required
              className="text-xs sm:text-sm h-9 sm:h-10"
            />
          </div>

          {/* Topic and Grade Level */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className="space-y-1.5">
              <label className="font-semibold text-ink-primary block text-xs sm:text-sm">
                Curricular Topic
              </label>
              <Input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Integer operations on number lines"
                className="text-xs sm:text-sm h-9 sm:h-10"
              />
            </div>
            <div className="space-y-1.5">
              <label className="font-semibold text-ink-primary block text-xs sm:text-sm">
                Grade / Level
              </label>
              <Input
                value={gradeLevel}
                onChange={(e) => setGradeLevel(e.target.value)}
                placeholder="e.g. Secondary 1"
                className="text-xs sm:text-sm h-9 sm:h-10"
              />
            </div>
          </div>

          {/* Task Instructions */}
          <div className="space-y-1.5">
            <label className="font-semibold text-ink-primary block text-xs sm:text-sm">
              Question / Task Instructions
            </label>
            <Textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              rows={2}
              placeholder="e.g. Use the number line to evaluate -6 + 12 - 4"
              className="text-xs sm:text-sm resize-none py-2"
            />
          </div>

          {/* Formula and Expected Answer */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className="space-y-1.5">
              <label className="font-semibold text-ink-primary block text-xs sm:text-sm">
                Mathematical Expression
              </label>
              <Input
                value={latexFormula}
                onChange={(e) => setLatexFormula(e.target.value)}
                placeholder="-6 + 12 - 4"
                className="font-mono text-xs sm:text-sm h-9 sm:h-10"
              />
              <span className="text-[10px] text-ink-muted block">
                Evaluated deterministically via SymPy engine
              </span>
            </div>
            <div className="space-y-1.5">
              <label className="font-semibold text-ink-primary block text-xs sm:text-sm">
                Expected Canonical Answer
              </label>
              <Input
                value={expectedAnswer}
                onChange={(e) => setExpectedAnswer(e.target.value)}
                placeholder="2"
                className="font-mono text-xs sm:text-sm h-9 sm:h-10"
              />
              <span className="text-[10px] text-ink-muted block">
                Target value for correctness verification
              </span>
            </div>
          </div>
        </DialogBody>

        <DialogFooter>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="sm"
            disabled={loading}
            className="px-4 py-2"
          >
            {loading ? (
              <>
                <Spinner size="sm" className="mr-1.5" />
                Creating...
              </>
            ) : (
              <>
                <BookOpen className="w-4 h-4 mr-1.5" />
                Create Assessment
              </>
            )}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}
