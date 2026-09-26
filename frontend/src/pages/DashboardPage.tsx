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
  CheckCircle2,
  XCircle,
  HelpCircle
} from 'lucide-react';
import { api } from '../services/api';
import { DashboardStats } from '../types';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDashboardStats();
      setStats(data);
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
            Real-time analytics on RAG accuracy, user feedback, error detection experiments, and automation bias indicators.
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

      {/* Top 9 Metric Cards */}
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

        {/* Total Documents */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Knowledge Docs</span>
            <FileText className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.total_documents}</p>
          <span className="text-[11px] text-slate-400">Active in ChromaDB</span>
        </div>

        {/* Total Feedback */}
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Total Feedback</span>
            <ThumbsUp className="w-4 h-4 text-cyan-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.total_feedback}</p>
          <span className="text-[11px] text-slate-400">Helpful & issue reports</span>
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
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-amber-600">{stats.reported_incorrect_responses}</p>
          <span className="text-[11px] text-slate-400">Hallucination alerts</span>
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

        {/* 2. Error Detection Breakdown */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-sm text-slate-800 flex items-center space-x-2">
              <Target className="w-4 h-4 text-indigo-600" />
              <span>User Study: Injected Error Detection</span>
            </h3>
            <span className="text-xs text-slate-400">Controlled testing</span>
          </div>

          <div className="space-y-3 pt-2">
            {[
              { label: 'Detected Injected Errors', key: 'Detected Injected Errors', color: 'bg-blue-600' },
              { label: 'Missed Injected Errors', key: 'Missed Injected Errors', color: 'bg-rose-500' },
              { label: 'False Alarms (Reported error on supported answer)', key: 'False Alarms', color: 'bg-amber-500' },
              { label: 'Correctly Verified Supported', key: 'Correctly Verified Supported', color: 'bg-emerald-500' }
            ].map((item) => {
              const count = stats.error_detection_breakdown[item.key] || 0;
              const total = Object.values(stats.error_detection_breakdown).reduce((a, b) => a + b, 0) || 1;
              const pct = Math.round((count / total) * 100);

              return (
                <div key={item.key} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-700">{item.label}</span>
                    <span className="font-mono text-slate-500">{count}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                    <div className={`${item.color} h-full transition-all duration-500`} style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 3. Feedback Category Distribution */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-sm text-slate-800 flex items-center space-x-2">
              <ThumbsUp className="w-4 h-4 text-emerald-600" />
              <span>Customer Feedback Breakdown</span>
            </h3>
            <span className="text-xs text-slate-400">Total submitted: {stats.total_feedback}</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-2">
            {Object.entries(stats.feedback_distribution).map(([cat, cnt]) => (
              <div key={cat} className="p-3 rounded-xl border border-slate-200 bg-slate-50/60 text-center space-y-1">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide block truncate">
                  {cat}
                </span>
                <span className="text-xl font-bold text-slate-800 block">{cnt}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
