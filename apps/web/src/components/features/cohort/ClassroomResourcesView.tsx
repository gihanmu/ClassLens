import * as React from "react";
import { ExitTicketItem } from "@/lib/api";
import { CheckCircle2, Printer, Download, Sparkles, HelpCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";

export interface ClassroomResourcesViewProps {
  exitTicketItems: ExitTicketItem[];
  onPrint?: () => void;
}

export function ClassroomResourcesView({
  exitTicketItems,
  onPrint,
}: ClassroomResourcesViewProps) {
  const handlePrint = () => {
    if (onPrint) onPrint();
    else window.print();
  };

  return (
    <div className="space-y-6">
      {/* Header with Print action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface-base p-6 rounded-2xl border border-border-default shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-light text-brand-primary">
              Ready-to-Use Curriculum Asset
            </span>
            <span className="text-xs font-mono text-ink-muted">Singapore MOE Aligned</span>
          </div>
          <Typography variant="h2" className="mt-1 text-xl sm:text-2xl font-bold">
            Formative Exit Ticket — Integer Addition & Subtraction
          </Typography>
          <Typography variant="body-sm" className="text-ink-secondary mt-0.5">
            Targeted diagnostic follow-up designed to confirm whether students have resolved identified number-line misconceptions.
          </Typography>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={handlePrint}>
            <Printer className="w-4 h-4 mr-1.5" />
            Print Exit Ticket
          </Button>
          <Button variant="coral" size="sm" onClick={handlePrint}>
            <Download className="w-4 h-4 mr-1.5" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* 3 Exit Ticket Questions */}
      <div className="space-y-4">
        <Typography variant="h3" className="text-lg font-bold">
          Exit Ticket Tasks ({exitTicketItems.length} Targeted Questions)
        </Typography>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {exitTicketItems.map((item, idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl border-2 border-border-default p-5 shadow-xs flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="w-7 h-7 rounded-full bg-brand-light text-brand-primary font-bold font-mono text-xs flex items-center justify-center">
                    Q{item.question_number}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-800 bg-accent-mint px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    SymPy Verified
                  </span>
                </div>

                <div className="p-3 bg-surface-subtle rounded-lg border border-border-default font-mono text-sm font-bold text-ink-primary text-center my-3">
                  {item.prompt}
                </div>

                <div className="text-xs text-ink-secondary space-y-1">
                  <p>
                    <strong className="text-ink-primary font-sans">Target Misconception:</strong>{" "}
                    <span className="font-mono text-[11px] text-accent-coral font-semibold">
                      {item.target_misconception.replace(/_/g, " ")}
                    </span>
                  </p>
                  <p>
                    <strong className="text-ink-primary font-sans">Expected Canonical Answer:</strong>{" "}
                    <span className="font-mono font-bold text-emerald-700">
                      {item.expected_answer}
                    </span>
                  </p>
                </div>
              </div>

              {/* Student Response Blank Space for Print */}
              <div className="mt-5 pt-3 border-t border-dashed border-border-default">
                <div className="h-20 rounded border border-dashed border-border-default bg-surface-canvas/50 flex items-center justify-center text-[11px] text-ink-muted">
                  [Student Number Line &amp; Calculation Workspace]
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Why These Questions & Next Steps */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card variant="educational">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-primary" />
              Why These Questions?
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-ink-secondary leading-relaxed">
            <p>
              • <strong>Question 1:</strong> Isolates the origin starting coordinate rule. Students who consistently begin at the first addend rather than 0 will land off-target immediately.
            </p>
            <p>
              • <strong>Question 2:</strong> Tests direction change across the zero boundary, separating sign interpretation from hop magnitude counting.
            </p>
            <p>
              • <strong>Question 3:</strong> Includes compensatory arithmetic traps to ensure students aren't masking procedural slips with final mental math corrections.
            </p>
          </CardContent>
        </Card>

        <Card variant="default">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <ArrowRight className="w-4 h-4 text-accent-coral" />
              Next Instructional Steps
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-ink-secondary leading-relaxed">
            <p>
              1. <strong>Administer at Start of Next Period:</strong> Give students 5 minutes to complete these 3 questions independently without calculators.
            </p>
            <p>
              2. <strong>Peer Review Pairing:</strong> Group students who struggled with starting points with peers who demonstrated valid number-line jumps.
            </p>
            <p>
              3. <strong>Log Overrides:</strong> As you review physical work, click "Teacher Review" in ClassLens to keep your classroom data synchronized.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
