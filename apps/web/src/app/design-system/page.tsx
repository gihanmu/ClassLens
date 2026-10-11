"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Sparkles, Check, AlertTriangle, Info, XCircle, Search, Layers, ShieldCheck } from "lucide-react";
import { Typography } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { IconButton } from "@/components/ui/icon-button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/ui/status-badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup } from "@/components/ui/radio-group";
import { Alert } from "@/components/ui/alert";
import { Dialog } from "@/components/ui/dialog";
import { Drawer } from "@/components/ui/drawer";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { BrandLogo } from "@/components/shared/brand-logo";
import { MetricCard } from "@/components/shared/metric-card";
import { FilterBar } from "@/components/shared/filter-bar";
import { EmptyState } from "@/components/shared/empty-state";
import { OfflineDemoBanner } from "@/components/shared/offline-demo-banner";
import { AnswerStatusBadge } from "@/components/features/students/AnswerStatusBadge";
import { ReasoningStatusBadge } from "@/components/features/students/ReasoningStatusBadge";
import { AnalysisProvenancePill } from "@/components/features/analysis/AnalysisProvenancePill";
import { MisconceptionCard } from "@/components/features/analysis/MisconceptionCard";
import { ReasoningStepCard } from "@/components/features/analysis/ReasoningStepCard";
import { TeachingRecommendationCard } from "@/components/features/cohort/TeachingRecommendationCard";

export default function DesignSystemPage() {
  const [activeTab, setActiveTab] = React.useState("foundations");
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [sampleInput, setSampleInput] = React.useState("");
  const [sampleCheck, setSampleCheck] = React.useState(true);
  const [sampleRadio, setSampleRadio] = React.useState("opt1");
  const [sampleFilter, setSampleFilter] = React.useState("all");

  return (
    <div className="min-h-screen bg-surface-canvas text-ink-primary font-sans">
      {/* Top Banner */}
      <OfflineDemoBanner />

      {/* Header */}
      <header className="border-b border-border-default bg-surface-base sticky top-0 z-20 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-ink-secondary hover:text-ink-primary transition-colors px-2 py-1 rounded-md hover:bg-surface-subtle"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to App
            </Link>
            <div className="h-5 w-px bg-border-default" />
            <BrandLogo size="md" showSubtitle />
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="primary">Design System v1.0</Badge>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="mb-8">
          <Typography variant="h1" className="text-3xl sm:text-4xl font-bold">
            ClassLens Design System
          </Typography>
          <Typography variant="body" className="text-ink-secondary mt-1">
            Formal token contracts, accessible UI primitives, and domain components designed for teacher clarity and mathematical rigor.
          </Typography>
        </div>

        {/* Showcase Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-8 overflow-x-auto pb-1 max-w-full">
            <TabsTrigger value="foundations">Foundations & Colors</TabsTrigger>
            <TabsTrigger value="typography">Typography</TabsTrigger>
            <TabsTrigger value="buttons">Buttons & Inputs</TabsTrigger>
            <TabsTrigger value="surfaces">Cards & Feedback</TabsTrigger>
            <TabsTrigger value="domain">Domain Components</TabsTrigger>
          </TabsList>

          {/* TAB 1: FOUNDATIONS & COLORS */}
          <TabsContent value="foundations" className="space-y-8">
            {/* Principles */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card variant="educational">
                <CardHeader>
                  <CardTitle className="text-base">1. Teacher-First Agency</CardTitle>
                  <CardDescription>
                    AI outputs remain provisional hypotheses. Teacher overrides have final diagnostic authority.
                  </CardDescription>
                </CardHeader>
              </Card>
              <Card variant="highlighted">
                <CardHeader>
                  <CardTitle className="text-base">2. Mathematical Rigor</CardTitle>
                  <CardDescription>
                    All calculations are formally verified by SymPy. Distinguishes reasoning from final answer.
                  </CardDescription>
                </CardHeader>
              </Card>
              <Card variant="default">
                <CardHeader>
                  <CardTitle className="text-base">3. WCAG 2.2 AA Contrast</CardTitle>
                  <CardDescription>
                    All text tokens pass 4.5:1 contrast ratio against cream canvas and surface backgrounds.
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>

            {/* Color Tokens */}
            <div>
              <Typography variant="h3" className="mb-4">
                Color Tokens
              </Typography>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                <div className="p-3 rounded-lg border border-border-default bg-surface-base shadow-xs space-y-2">
                  <div className="h-12 rounded bg-brand-primary flex items-center justify-center text-white font-mono text-xs font-bold">
                    #5145F5
                  </div>
                  <div>
                    <p className="text-xs font-bold text-ink-primary">brand-primary</p>
                    <p className="text-[10px] text-ink-muted">Interactive & brand</p>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-border-default bg-surface-base shadow-xs space-y-2">
                  <div className="h-12 rounded bg-accent-coral flex items-center justify-center text-white font-mono text-xs font-bold">
                    #F76543
                  </div>
                  <div>
                    <p className="text-xs font-bold text-ink-primary">accent-coral</p>
                    <p className="text-[10px] text-ink-muted">Call to action & highlight</p>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-border-default bg-surface-base shadow-xs space-y-2">
                  <div className="h-12 rounded bg-accent-yellow flex items-center justify-center text-ink-primary font-mono text-xs font-bold">
                    #FFCF78
                  </div>
                  <div>
                    <p className="text-xs font-bold text-ink-primary">accent-yellow</p>
                    <p className="text-[10px] text-ink-muted">Warmth & attention</p>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-border-default bg-surface-base shadow-xs space-y-2">
                  <div className="h-12 rounded bg-accent-mint flex items-center justify-center text-emerald-900 font-mono text-xs font-bold">
                    #D8F4E8
                  </div>
                  <div>
                    <p className="text-xs font-bold text-ink-primary">accent-mint</p>
                    <p className="text-[10px] text-ink-muted">Success & valid steps</p>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-border-default bg-surface-base shadow-xs space-y-2">
                  <div className="h-12 rounded bg-ink-primary flex items-center justify-center text-white font-mono text-xs font-bold">
                    #10182B
                  </div>
                  <div>
                    <p className="text-xs font-bold text-ink-primary">ink-primary</p>
                    <p className="text-[10px] text-ink-muted">14.2:1 contrast ratio</p>
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-border-default bg-surface-base shadow-xs space-y-2">
                  <div className="h-12 rounded bg-surface-canvas border border-border-default flex items-center justify-center text-ink-primary font-mono text-xs font-bold">
                    #FAF9F6
                  </div>
                  <div>
                    <p className="text-xs font-bold text-ink-primary">surface-canvas</p>
                    <p className="text-[10px] text-ink-muted">Warm cream foundation</p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* TAB 2: TYPOGRAPHY */}
          <TabsContent value="typography" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Typography Hierarchy</CardTitle>
                <CardDescription>Plus Jakarta Sans for headings and UI; IBM Plex Mono for mathematical terms and numbers.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="pb-3 border-b border-border-default">
                  <Typography variant="display">Display — 36px/48px Bold</Typography>
                  <span className="text-[11px] font-mono text-ink-muted">variant="display"</span>
                </div>
                <div className="pb-3 border-b border-border-default">
                  <Typography variant="h1">Heading 1 — 30px Bold</Typography>
                  <span className="text-[11px] font-mono text-ink-muted">variant="h1"</span>
                </div>
                <div className="pb-3 border-b border-border-default">
                  <Typography variant="h2">Heading 2 — 24px Bold</Typography>
                  <span className="text-[11px] font-mono text-ink-muted">variant="h2"</span>
                </div>
                <div className="pb-3 border-b border-border-default">
                  <Typography variant="h3">Heading 3 — 20px Semibold</Typography>
                  <span className="text-[11px] font-mono text-ink-muted">variant="h3"</span>
                </div>
                <div className="pb-3 border-b border-border-default">
                  <Typography variant="body-lg">Body Large — 18px Regular for primary introductions and teacher insights.</Typography>
                  <span className="text-[11px] font-mono text-ink-muted">variant="body-lg"</span>
                </div>
                <div className="pb-3 border-b border-border-default">
                  <Typography variant="body">Body — 16px Regular standard paragraph text for descriptions and guidelines.</Typography>
                  <span className="text-[11px] font-mono text-ink-muted">variant="body"</span>
                </div>
                <div className="pb-3 border-b border-border-default">
                  <Typography variant="body-sm">Body Small — 14px Regular for card metadata and secondary helper text.</Typography>
                  <span className="text-[11px] font-mono text-ink-muted">variant="body-sm"</span>
                </div>
                <div>
                  <Typography variant="mono">Mono — -6 + 12 - 4 = +2 (SymPy Exact)</Typography>
                  <span className="text-[11px] font-mono text-ink-muted block mt-1">variant="mono"</span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 3: BUTTONS & INPUTS */}
          <TabsContent value="buttons" className="space-y-8">
            {/* Buttons */}
            <Card>
              <CardHeader>
                <CardTitle>Button Primitives</CardTitle>
                <CardDescription>Interactive button states with 44px touch targets and full keyboard focus ring.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="primary">Primary Button</Button>
                  <Button variant="coral">Coral CTA</Button>
                  <Button variant="secondary">Secondary</Button>
                  <Button variant="outline">Outline</Button>
                  <Button variant="ghost">Ghost</Button>
                  <Button variant="destructive">Destructive</Button>
                  <Button variant="primary" isLoading>Loading</Button>
                  <Button variant="primary" disabled>Disabled</Button>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <IconButton icon={<Check className="w-4 h-4" />} aria-label="Confirm" variant="primary" />
                  <IconButton icon={<Search className="w-4 h-4" />} aria-label="Search" variant="neutral" />
                  <IconButton icon={<AlertTriangle className="w-4 h-4" />} aria-label="Warning" variant="destructive" />
                </div>
              </CardContent>
            </Card>

            {/* Inputs & Form Controls */}
            <Card>
              <CardHeader>
                <CardTitle>Form Controls</CardTitle>
                <CardDescription>Accessible inputs with explicit labels, focus styles, and error states.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Student Pseudonym"
                    placeholder="e.g. response_01"
                    value={sampleInput}
                    onChange={(e) => setSampleInput(e.target.value)}
                    helperText="Generated locally using SHA-256 pseudonymization"
                  />
                  <Select
                    label="Misconception Taxonomy"
                    options={[
                      { value: "m1", label: "Start Point Misunderstanding" },
                      { value: "m2", label: "Direction / Sign Confusion" },
                      { value: "m3", label: "Incorrect Hop Magnitude" },
                    ]}
                  />
                </div>

                <Textarea
                  label="Teacher Clinical Observation"
                  placeholder="Record classroom dialogue, student explanations, or notes..."
                  rows={2}
                />

                <div className="pt-2 flex flex-wrap items-center gap-6">
                  <Checkbox
                    id="check-sample"
                    label="Verified with SymPy engine"
                    description="Offline exact arithmetic verification"
                    checked={sampleCheck}
                    onChange={(e) => setSampleCheck(e.target.checked)}
                  />

                  <RadioGroup
                    name="sample-radio"
                    value={sampleRadio}
                    onChange={setSampleRadio}
                    options={[
                      { value: "opt1", label: "Standard Path" },
                      { value: "opt2", label: "Alternative Path" },
                    ]}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 4: SURFACES & FEEDBACK */}
          <TabsContent value="surfaces" className="space-y-8">
            {/* Status Badges */}
            <Card>
              <CardHeader>
                <CardTitle>Badges & Status Indicators</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                <StatusBadge status="success">Verified Success</StatusBadge>
                <StatusBadge status="error">Procedural Error</StatusBadge>
                <StatusBadge status="warning">Needs Teacher Review</StatusBadge>
                <StatusBadge status="info">Information</StatusBadge>
                <StatusBadge status="pending">Processing</StatusBadge>
                <StatusBadge status="mock">Simulated Mode</StatusBadge>
              </CardContent>
            </Card>

            {/* Alerts */}
            <div className="space-y-3">
              <Alert variant="info" title="Offline Evaluation Active">
                ClassLens operates in safe zero-cloud offline simulation mode using pre-computed multimodal agent fixtures.
              </Alert>
              <Alert variant="warning" title="Compensatory Error Detected">
                Student reached the expected final answer (+2) despite executing an incorrect intermediate hop length.
              </Alert>
              <Alert variant="success" title="SymPy Verification Passed">
                All 3 hops match exact arithmetic definitions without floating-point inaccuracies.
              </Alert>
            </div>

            {/* Modals & Overlays */}
            <Card>
              <CardHeader>
                <CardTitle>Dialog & Drawer Overlays</CardTitle>
                <CardDescription>Keyboard-accessible overlays with focus trapping and ESC dismissal.</CardDescription>
              </CardHeader>
              <CardContent className="flex gap-3">
                <Button variant="secondary" onClick={() => setDialogOpen(true)}>
                  Open Sample Dialog
                </Button>
                <Button variant="secondary" onClick={() => setDrawerOpen(true)}>
                  Open Slide-Out Drawer
                </Button>
              </CardContent>
            </Card>

            <Dialog
              isOpen={dialogOpen}
              onClose={() => setDialogOpen(false)}
              title="Mathematical Verification Details"
              description="Review SymPy step equations and formal logic certificates."
            >
              <div className="space-y-3 text-xs">
                <p>Formula evaluated: <strong>-6 + 12 - 4</strong></p>
                <p>Expected canonical result: <strong>2</strong></p>
                <div className="p-3 bg-surface-subtle rounded font-mono text-[11px]">
                  Step 1: 0 + (-6) = -6 [VALID]<br />
                  Step 2: -6 + 12 = 6 [VALID]<br />
                  Step 3: 6 + (-4) = 2 [VALID]
                </div>
              </div>
            </Dialog>

            <Drawer
              isOpen={drawerOpen}
              onClose={() => setDrawerOpen(false)}
              title="Student Assessment Audit Log"
            >
              <div className="space-y-4 text-xs">
                <div className="p-3 rounded bg-surface-subtle border border-border-default">
                  <span className="font-semibold text-ink-primary">2026-10-11 14:00</span>
                  <p className="text-ink-secondary mt-1">Multi-agent analysis completed (offline mock adapter).</p>
                </div>
                <div className="p-3 rounded bg-surface-subtle border border-border-default">
                  <span className="font-semibold text-ink-primary">2026-10-11 14:10</span>
                  <p className="text-ink-secondary mt-1">Teacher confirmed diagnosis for Response #01.</p>
                </div>
              </div>
            </Drawer>
          </TabsContent>

          {/* TAB 5: DOMAIN COMPONENTS */}
          <TabsContent value="domain" className="space-y-8">
            {/* Metric Cards Row */}
            <div>
              <Typography variant="h3" className="mb-4">
                Metric Summary Cards (from Mockup)
              </Typography>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  title="Submissions"
                  value={13}
                  subtext="Curated classroom set"
                  accent="brand"
                  icon={<Layers className="w-5 h-5" />}
                />
                <MetricCard
                  title="Analyses Completed"
                  value={13}
                  denominator={13}
                  subtext="100% complete"
                  accent="mint"
                  icon={<Check className="w-5 h-5" />}
                />
                <MetricCard
                  title="Correct Final Answers"
                  value={9}
                  denominator={13}
                  subtext="69% success rate"
                  accent="coral"
                  icon={<Sparkles className="w-5 h-5" />}
                />
                <MetricCard
                  title="Teacher Reviews"
                  value={1}
                  denominator={13}
                  subtext="8% reviewed"
                  accent="yellow"
                  icon={<ShieldCheck className="w-5 h-5" />}
                />
              </div>
            </div>

            {/* Badges and Pills */}
            <Card>
              <CardHeader>
                <CardTitle>Domain Badges & Provenance Indicators</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-3 items-center">
                  <AnswerStatusBadge status="correct" />
                  <AnswerStatusBadge status="incorrect" />
                  <AnswerStatusBadge status="unassessable" />
                </div>
                <div className="flex flex-wrap gap-3 items-center">
                  <ReasoningStatusBadge status="valid" />
                  <ReasoningStatusBadge status="procedural_error" />
                  <ReasoningStatusBadge status="incomplete" />
                </div>
                <div className="flex flex-wrap gap-3 items-center">
                  <AnalysisProvenancePill provenance="offline_simulated" />
                  <AnalysisProvenancePill provenance="ai_proposed" />
                  <AnalysisProvenancePill provenance="teacher_confirmed" />
                  <AnalysisProvenancePill provenance="teacher_overridden" />
                </div>
              </CardContent>
            </Card>

            {/* Filter Bar */}
            <div>
              <Typography variant="h3" className="mb-3">
                Filter Bar (from Mockup)
              </Typography>
              <FilterBar
                options={[
                  { id: "all", label: "All Responses", count: 13 },
                  { id: "review", label: "Needs Review", count: 2 },
                  { id: "errors", label: "Procedure Issues", count: 4 },
                  { id: "correct", label: "Accurate", count: 9 },
                ]}
                selectedId={sampleFilter}
                onSelect={setSampleFilter}
              />
            </div>

            {/* Misconception & Step Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Typography variant="h4" className="mb-2">
                  First Supported Error Card
                </Typography>
                <MisconceptionCard
                  misconceptionTitle="Start Point Misunderstanding"
                  error={{
                    step_number: 1,
                    error_type: "START_POINT_ZERO_MISUNDERSTANDING",
                    observed_behavior: "Started jump directly at tick mark -1 instead of 0",
                    expected_behavior: "Begin first directed hop at coordinate 0",
                    explanation: "Student began first vector at coordinate -1, shifting all subsequent coordinates leftward by 1 unit.",
                  }}
                  isCompensatoryError={false}
                />
              </div>

              <div>
                <Typography variant="h4" className="mb-2">
                  Verified Step Breakdown
                </Typography>
                <div className="space-y-2">
                  <ReasoningStepCard
                    step={{
                      step_number: 1,
                      operation: "Hop 1: 0 + (-6) = -6",
                      expected_result: -6,
                      observed_result: -6,
                      is_correct: true,
                      evidence_citation: "Arc from 0 to -6 clearly drawn with left arrowhead",
                    }}
                  />
                  <ReasoningStepCard
                    step={{
                      step_number: 2,
                      operation: "Hop 2: -6 + 12 = 6",
                      expected_result: 6,
                      observed_result: 0,
                      is_correct: false,
                      evidence_citation: "Arc spans +6 units instead of +12 units",
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Differentiated Recommendation Card */}
            <div>
              <Typography variant="h4" className="mb-3">
                Teaching Action Recommendation Card
              </Typography>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <TeachingRecommendationCard
                  action={{
                    action_type: "concrete_manipulative",
                    target_misconception_id: "START_POINT_ZERO_MISUNDERSTANDING",
                    title: "Floor Number Line Walkway",
                    student_count_affected: 2,
                    instructional_steps: [
                      "Place large painter's tape number line on classroom floor.",
                      "Have student physically stand on 0 as the origin before taking any directional steps.",
                      "Reinforce that '0' represents starting state before any operations are applied.",
                    ],
                  }}
                />
                <TeachingRecommendationCard
                  action={{
                    action_type: "worked_example",
                    target_misconception_id: "INCORRECT_INTERVAL_MAGNITUDE",
                    title: "Side-by-Side Hop Calibration",
                    student_count_affected: 3,
                    instructional_steps: [
                      "Display an incorrect +6 jump next to the correct +12 jump.",
                      "Prompt: 'Why does jumping 12 units land on +6 rather than 0?'",
                      "Students count individual tick intervals aloud.",
                    ],
                  }}
                />
                <TeachingRecommendationCard
                  action={{
                    action_type: "guided_inquiry",
                    target_misconception_id: "COMPENSATORY_ARITHMETIC_ERROR",
                    title: "Reasoning vs Answer Audit",
                    student_count_affected: 1,
                    instructional_steps: [
                      "Examine how an arithmetic slip compensated for a drawing slip.",
                      "Discuss why correct answers with faulty reasoning can mask confusion on future assessments.",
                    ],
                  }}
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
