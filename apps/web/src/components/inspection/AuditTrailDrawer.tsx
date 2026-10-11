"use client";

import React, { useState, useEffect } from "react";
import { History, Clock, UserCheck } from "lucide-react";
import { api, AuditEvent } from "@/lib/api";

interface AuditTrailDrawerProps {
  responseId: string;
}

export function AuditTrailDrawer({ responseId }: AuditTrailDrawerProps) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadAuditEvents = async () => {
    try {
      setLoading(true);
      const data = await api.getAuditTrail(responseId);
      setEvents(data);
    } catch (err) {
      console.error("Failed to load audit trail:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditEvents();
  }, [responseId]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center space-x-2">
          <History className="h-4 w-4 text-slate-500" aria-hidden="true" />
          <h3 className="font-semibold text-slate-800 text-sm tracking-wide uppercase">
            Audit Trail
          </h3>
        </div>
        <button
          type="button"
          onClick={loadAuditEvents}
          className="text-xs text-indigo-600 hover:text-indigo-800 underline focus-visible:ring-2 focus-visible:ring-indigo-400"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <p className="text-xs text-slate-400">Loading audit history...</p>
      ) : events.length === 0 ? (
        <p className="text-xs text-slate-500 italic">
          No human overrides recorded yet. Initial automated AI diagnosis active.
        </p>
      ) : (
        <div className="space-y-2">
          {events.map((evt) => (
            <div
              key={evt.id}
              className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-xs space-y-1"
            >
              <div className="flex items-center justify-between font-mono text-[11px] text-slate-500">
                <span className="flex items-center space-x-1">
                  <UserCheck className="h-3 w-3 text-indigo-500" aria-hidden="true" />
                  <span>{evt.teacher_id}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Clock className="h-3 w-3 text-slate-400" aria-hidden="true" />
                  <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                </span>
              </div>
              <div className="font-semibold text-slate-800">
                Action: <span className="uppercase text-indigo-700">{evt.action}</span>
              </div>
              {evt.notes && (
                <p className="text-slate-600 italic bg-white p-1.5 rounded border border-slate-100">
                  &ldquo;{evt.notes}&rdquo;
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
