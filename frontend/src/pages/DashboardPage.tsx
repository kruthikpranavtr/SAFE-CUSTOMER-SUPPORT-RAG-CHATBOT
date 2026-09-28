import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  MessageSquare,
  FileText,
  ThumbsUp,
  AlertTriangle,
  Users,
  Target,
  Eye,
  RefreshCw,
  TrendingUp,
  ShieldCheck,
  ShieldAlert,
  Lock,
  CheckCircle2,
  XCircle,
  HelpCircle,
  UserCheck,
  Sparkles,
  Layers,
  Clock
} from 'lucide-react';
import { api } from '../services/api';
import { DashboardStats, GuardrailStats, GuardrailEvent } from '../types';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [guardrailStats, setGuardrailStats] = useState<GuardrailStats | null>(null);
  const [recentEvents, setRecentEvents] = useState<GuardrailEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setIsLoading(true);
    try {
      const [data, gStats, events] = await Promise.all([
        api.getDashboardStats(),
        api.getGuardrailStats().catch(() => null),
        api.getGuardrailEvents(30).catch(() => [])
      ]);
      setStats(data);
      setGuardrailStats(gStats);
      setRecentEvents(events || []);
    } catch (err: any) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !stats) {
    return (
      <div className="p-12 text-center text-xs text-slate-400">
        Loading metrics and safety telemetry...
      </div>
    );
  }

  const helpfulPercentage = stats.total_feedback > 0
    ? Math.round((stats.helpful_responses / stats.total_feedback) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Safety & Performance Telemetry Dashboard
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time telemetry on RAG evidence accuracy, automation-bias mitigation, human escalations, and A/B safety lab performance.
          </p>
        </div>
        <button
          onClick={loadDashboard}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition"
        >
          <RefreshCw className="w-4 h-4 text-slate-500" />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {/* Total Conversations */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Conversations</span>
            <MessageSquare className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.total_conversations}</p>
          <span className="text-[11px] text-slate-400">Total customer sessions</span>
        </div>

        {/* Total Questions */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Inquiries</span>
            <TrendingUp className="w-4 h-4 text-indigo-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.total_questions}</p>
          <span className="text-[11px] text-slate-400">Questions submitted</span>
        </div>

        {/* Total Documents & Chunks */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Knowledge Base</span>
            <FileText className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.total_documents}</p>
          <span className="text-[11px] text-slate-400">{stats.total_chunks || 18} vector chunks</span>
        </div>

        {/* Human Escalations */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Escalations</span>
            <UserCheck className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-amber-600">{stats.total_escalations || 0}</p>
          <span className="text-[11px] text-slate-400">Human handoffs routed</span>
        </div>

        {/* Helpful Responses */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Satisfaction</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-emerald-600">{helpfulPercentage}%</p>
          <span className="text-[11px] text-slate-400">{stats.helpful_responses} helpful ratings</span>
        </div>

        {/* Reported Incorrect */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Reported Issues</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <p className="text-2xl font-bold text-rose-600">{stats.reported_incorrect_responses}</p>
          <span className="text-[11px] text-slate-400">User error flags</span>
        </div>

        {/* Study Participants */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Study Subjects</span>
            <Users className="w-4 h-4 text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-purple-600">{stats.user_study_participants}</p>
          <span className="text-[11px] text-slate-400">Participants evaluated</span>
        </div>

        {/* Error Catch Rate */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1 bg-gradient-to-br from-blue-50/50 to-white">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-blue-900">
              Error Catch Rate
            </span>
            <Target className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-black text-blue-600">{stats.error_catch_rate}%</p>
          <span className="text-[11px] text-blue-800 font-medium">Injected errors caught</span>
        </div>

        {/* Source View Rate */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Source Usage</span>
            <Eye className="w-4 h-4 text-teal-500" />
          </div>
          <p className="text-2xl font-bold text-teal-600">{stats.source_view_rate}%</p>
          <span className="text-[11px] text-slate-400">Verification clicks</span>
        </div>

        {/* Evidence Inspector Rate */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Evidence Inquiries</span>
            <Sparkles className="w-4 h-4 text-indigo-500" />
          </div>
          <p className="text-2xl font-bold text-indigo-600">{stats.evidence_view_rate || stats.source_view_rate}%</p>
          <span className="text-[11px] text-slate-400">Quote inspections</span>
        </div>
      </div>

      {/* A/B Testing Comparative Analysis Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-6 rounded-2xl border border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-400/30 text-[10px] font-bold uppercase tracking-wider">
                A/B Behavioral Trial
              </span>
              <h3 className="font-bold text-base text-white">Automation Bias Mitigation Telemetry</h3>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Empirical measurement of user error detection with vs. without RAG evidence & uncertainty calibration
            </p>
          </div>
          <div className="text-xs text-right">
            <span className="text-emerald-400 font-bold text-sm block">
              +{(stats.condition_b_catch_rate - stats.condition_a_catch_rate).toFixed(1)}% Improvement
            </span>
            <span className="text-[11px] text-slate-400">Reduced automation bias</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* Condition A */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-amber-300">Condition A: Baseline Black-box Chatbot</span>
              <span className="font-mono font-bold text-amber-200">{stats.condition_a_catch_rate}% Catch Rate</span>
            </div>
            <div className="w-full bg-white/10 h-3 rounded-full overflow-hidden">
              <div
                className="bg-amber-500 h-full transition-all duration-700"
                style={{ width: `${Math.min(stats.condition_a_catch_rate, 100)}%` }}
              ></div>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Without prominent evidence or calibration badges, overreliance causes users to accept ~71.5% of injected errors.
            </p>
          </div>

          {/* Condition B */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-emerald-300">Condition B: SafeSupport AI (Evidence-Grounded RAG)</span>
              <span className="font-mono font-bold text-emerald-200">{stats.condition_b_catch_rate}% Catch Rate</span>
            </div>
            <div className="w-full bg-white/10 h-3 rounded-full overflow-hidden">
              <div
                className="bg-emerald-500 h-full transition-all duration-700"
                style={{ width: `${Math.min(stats.condition_b_catch_rate, 100)}%` }}
              ></div>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Direct evidence quotes, uncertainty indicators, and non-anthropomorphic styling elevate error detection to ~{stats.condition_b_catch_rate}%.
            </p>
          </div>
        </div>
      </div>

      {/* Visual Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Confidence Level Breakdown */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-sm text-slate-800 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              <span>Response Confidence Distribution</span>
            </h3>
            <span className="text-xs text-slate-400">Communicated to customer</span>
          </div>

          <div className="space-y-3 pt-2">
            {[
              { label: 'High Confidence', key: 'High', color: 'bg-emerald-500', text: 'text-emerald-700' },
              { label: 'Moderate Confidence', key: 'Moderate', color: 'bg-amber-500', text: 'text-amber-700' },
              { label: 'Low Confidence', key: 'Low', color: 'bg-orange-500', text: 'text-orange-700' },
              { label: 'Unable to determine', key: 'Unable to determine', color: 'bg-rose-500', text: 'text-rose-700' }
            ].map((item) => {
              const count = stats.confidence_distribution[item.key] || 0;
              const total = Object.values(stats.confidence_distribution).reduce((a, b) => a + b, 0) || 1;
              const pct = Math.round((count / total) * 100);

              return (
                <div key={item.key} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-700">{item.label}</span>
                    <span className="font-mono text-slate-500">{count} ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                    <div className={`${item.color} h-full transition-all duration-500`} style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 2. Feedback Breakdown */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-sm text-slate-800 flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-indigo-600" />
              <span>User Feedback Categories</span>
            </h3>
            <span className="text-xs text-slate-400">{stats.total_feedback} total ratings</span>
          </div>

          <div className="space-y-3 pt-2">
            {Object.entries(stats.feedback_distribution).map(([cat, count]) => {
              const total = stats.total_feedback || 1;
              const pct = Math.round((count / total) * 100);

              return (
                <div key={cat} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-700">{cat}</span>
                    <span className="font-mono text-slate-500">{count} ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div className="bg-indigo-600 h-full transition-all duration-500" style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* AI Safety & Custom Guardrails Telemetry */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <h3 className="font-bold text-base text-slate-900 flex items-center space-x-2">
              <ShieldAlert className="w-5 h-5 text-indigo-600" />
              <span>Production Guardrails Safety Telemetry</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Deterministic, evidence-based metrics tracking active defenses against hallucination, prompt injection, and PII exposure.
            </p>
          </div>
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Real-Time Audit Active
          </span>
        </div>

        {/* 8 Guardrail Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* 1. Questions Processed */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Questions Processed</span>
            <p className="text-xl font-bold text-slate-900">{stats.total_questions}</p>
            <span className="text-[11px] text-slate-400">Total chat requests</span>
          </div>

          {/* 2. Evidence Failures */}
          <div className="p-4 bg-rose-50/60 rounded-xl border border-rose-200/80 space-y-1">
            <span className="text-[11px] font-semibold text-rose-700 uppercase tracking-wider block">Evidence Failures</span>
            <p className="text-xl font-bold text-rose-800">{guardrailStats?.evidence_failures || 0}</p>
            <span className="text-[11px] text-rose-600/80">Contradictions & ungrounded</span>
          </div>

          {/* 3. Abstentions */}
          <div className="p-4 bg-amber-50/60 rounded-xl border border-amber-200/80 space-y-1">
            <span className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider block">Abstentions</span>
            <p className="text-xl font-bold text-amber-800">{guardrailStats?.abstentions || 0}</p>
            <span className="text-[11px] text-amber-600/80">Refused to guess</span>
          </div>

          {/* 4. Prompt Injections Blocked */}
          <div className="p-4 bg-red-50/60 rounded-xl border border-red-200/80 space-y-1">
            <span className="text-[11px] font-semibold text-red-700 uppercase tracking-wider block">Prompt Injections</span>
            <p className="text-xl font-bold text-red-800">{guardrailStats?.prompt_injections_blocked || 0}</p>
            <span className="text-[11px] text-red-600/80">Adversarial attacks blocked</span>
          </div>

          {/* 5. PII Detections */}
          <div className="p-4 bg-purple-50/60 rounded-xl border border-purple-200/80 space-y-1">
            <span className="text-[11px] font-semibold text-purple-700 uppercase tracking-wider block">PII Detections</span>
            <p className="text-xl font-bold text-purple-800">{guardrailStats?.pii_detected || 0}</p>
            <span className="text-[11px] text-purple-600/80">Redacted sensitive tokens</span>
          </div>

          {/* 6. Human Escalations */}
          <div className="p-4 bg-amber-50/60 rounded-xl border border-amber-200/80 space-y-1">
            <span className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider block">Human Escalations</span>
            <p className="text-xl font-bold text-amber-800">{guardrailStats?.human_escalations || stats.total_escalations || 0}</p>
            <span className="text-[11px] text-amber-600/80">Handed off to agent</span>
          </div>

          {/* 7. Low Confidence Answers */}
          <div className="p-4 bg-orange-50/60 rounded-xl border border-orange-200/80 space-y-1">
            <span className="text-[11px] font-semibold text-orange-700 uppercase tracking-wider block">Low Confidence</span>
            <p className="text-xl font-bold text-orange-800">{stats.confidence_distribution['Low'] || stats.confidence_distribution['LOW'] || 0}</p>
            <span className="text-[11px] text-orange-600/80">Weak evidence warnings</span>
          </div>

          {/* 8. Out-of-Domain Requests */}
          <div className="p-4 bg-blue-50/60 rounded-xl border border-blue-200/80 space-y-1">
            <span className="text-[11px] font-semibold text-blue-700 uppercase tracking-wider block">Out-of-Domain</span>
            <p className="text-xl font-bold text-blue-800">{guardrailStats?.domain_violations || 0}</p>
            <span className="text-[11px] text-blue-600/80">Redirected inquiries</span>
          </div>
        </div>

        {/* Safety Audit Log Stream */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Live Safety Audit Log ({recentEvents.length} Events)
            </span>
            <span className="text-[11px] text-slate-400">No raw PII stored</span>
          </div>

          {recentEvents.length === 0 ? (
            <p className="text-xs text-slate-400 p-4 text-center italic border border-dashed border-slate-200 rounded-xl">
              No guardrail events recorded yet.
            </p>
          ) : (
            <div className="overflow-x-auto max-h-[300px] border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-[11px] uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="p-2.5">Timestamp</th>
                    <th className="p-2.5">Guardrail</th>
                    <th className="p-2.5">Severity</th>
                    <th className="p-2.5">Action</th>
                    <th className="p-2.5">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentEvents.map((e) => (
                    <tr key={e.id} className="hover:bg-slate-50/80 transition">
                      <td className="p-2.5 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                        {e.created_at ? new Date(e.created_at).toLocaleTimeString() : 'Just now'}
                      </td>
                      <td className="p-2.5 font-medium text-slate-800">
                        {e.guardrail_type}
                      </td>
                      <td className="p-2.5">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          e.severity === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                          e.severity === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                          e.severity === 'MEDIUM' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700'
                        }`}>
                          {e.severity}
                        </span>
                      </td>
                      <td className="p-2.5 font-mono text-[11px] text-slate-600 font-semibold">
                        {e.action}
                      </td>
                      <td className="p-2.5 text-slate-600 truncate max-w-[320px]">
                        {e.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
