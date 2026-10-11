"use client";

import React from "react";
import { MisconceptionCluster } from "@/lib/api";

interface MisconceptionBarChartProps {
  clusters: MisconceptionCluster[];
  totalStudents: number;
}

export function MisconceptionBarChart({
  clusters,
  totalStudents,
}: MisconceptionBarChartProps) {
  if (!clusters || clusters.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h3 className="font-semibold text-slate-800 text-sm tracking-wide uppercase mb-2">
          Misconception Distribution
        </h3>
        <p className="text-sm text-slate-500 italic">
          No misconception clusters localized in the student cohort.
        </p>
      </div>
    );
  }

  const maxCount = Math.max(...clusters.map((c) => c.affected_count), 1);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="font-semibold text-slate-800 text-sm tracking-wide uppercase">
            Misconception Frequency Distribution
          </h3>
          <p className="text-xs text-slate-500">
            Explicit fractional denominators across cohort of {totalStudents} students
          </p>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          <span className="flex items-center space-x-1">
            <span className="h-3 w-3 rounded bg-indigo-600 inline-block" />
            <span className="text-slate-600">AI Proposed</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="h-3 w-3 rounded bg-emerald-600 inline-block" />
            <span className="text-slate-600">Teacher Confirmed</span>
          </span>
        </div>
      </div>

      {/* Accessible Bar Chart */}
      <div className="space-y-4" role="region" aria-label="Misconception cluster horizontal bar chart">
        {clusters.map((cluster) => {
          const barWidthPct = Math.round((cluster.affected_count / maxCount) * 100);
          return (
            <div key={cluster.taxonomy_id} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <div className="font-semibold text-slate-800 flex items-center space-x-2">
                  <span className="font-mono text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                    {cluster.taxonomy_id}
                  </span>
                  <span>{cluster.title}</span>
                </div>
                {/* Explicit Fractional Denominator */}
                <div className="font-mono font-bold text-slate-700">
                  {cluster.affected_count} of {totalStudents} students ({cluster.affected_percentage}%)
                </div>
              </div>

              {/* Progress Bar Container */}
              <div className="w-full bg-slate-100 rounded-full h-4 overflow-hidden flex border border-slate-200">
                {/* AI Proposed Segment */}
                {cluster.ai_proposed_count > 0 && (
                  <div
                    style={{ width: `${(cluster.ai_proposed_count / maxCount) * 100}%` }}
                    className="bg-indigo-500 h-full transition-all duration-300"
                    title={`AI Proposed: ${cluster.ai_proposed_count}`}
                  />
                )}
                {/* Teacher Confirmed Segment */}
                {cluster.teacher_confirmed_count > 0 && (
                  <div
                    style={{ width: `${(cluster.teacher_confirmed_count / maxCount) * 100}%` }}
                    className="bg-emerald-500 h-full transition-all duration-300"
                    title={`Teacher Confirmed: ${cluster.teacher_confirmed_count}`}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Accessible Screen Reader Table Alternative */}
      <details className="mt-4 text-xs text-slate-500 pt-3 border-t border-slate-100">
        <summary className="cursor-pointer hover:text-indigo-600 font-medium">
          View Accessible Data Table for Screen Readers
        </summary>
        <table className="w-full mt-3 text-left border-collapse border border-slate-200" role="table">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-700">
              <th className="p-2 border border-slate-200">Taxonomy ID</th>
              <th className="p-2 border border-slate-200">Description</th>
              <th className="p-2 border border-slate-200">Student Count</th>
              <th className="p-2 border border-slate-200">Cohort Percentage</th>
            </tr>
          </thead>
          <tbody>
            {clusters.map((c) => (
              <tr key={c.taxonomy_id} className="border-b border-slate-200">
                <td className="p-2 border border-slate-200 font-mono">{c.taxonomy_id}</td>
                <td className="p-2 border border-slate-200">{c.title}</td>
                <td className="p-2 border border-slate-200">{c.affected_count} of {totalStudents}</td>
                <td className="p-2 border border-slate-200">{c.affected_percentage}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
