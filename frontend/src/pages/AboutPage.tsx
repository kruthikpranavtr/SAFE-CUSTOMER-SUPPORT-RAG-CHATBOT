import React from 'react';
import {
  ShieldAlert,
  Bot,
  FileCheck2,
  AlertTriangle,
  FlaskConical,
  Database,
  Search,
  CheckCircle2,
  ArrowRight,
  Sparkles
} from 'lucide-react';

export const AboutPage: React.FC<{ onNavigateToChat: () => void; onNavigateToStudy: () => void }> = ({
  onNavigateToChat,
  onNavigateToStudy
}) => {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-10">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-900 text-white p-8 sm:p-10 rounded-3xl shadow-xl relative overflow-hidden space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Responsible AI Engineering</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
          Safe Customer Support with Evidence-Based Answers
        </h1>
        <p className="text-sm sm:text-base text-blue-100/90 leading-relaxed max-w-2xl">
          Get transparent answers directly from verified company documentation, equipped with active uncertainty communication, source citation, and automation bias mitigations.
        </p>
        <div className="pt-2 flex flex-wrap gap-3">
          <button
            onClick={onNavigateToChat}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md transition"
          >
            <span>Start Support Chat</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={onNavigateToStudy}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-xs border border-white/20 transition"
          >
            <span>Participate in User Study</span>
            <FlaskConical className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 4 Core Safety Pillars */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Safety Mechanisms & AI Guardrails</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Pillar 1 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">1. Automation Bias Mitigation</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Users frequently assume computer outputs are infallible. Our interface proactively highlights verification warnings: "AI answers may contain errors. Check the cited sources before making important decisions."
            </p>
          </div>

          {/* Pillar 2 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Bot className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">2. Anthropomorphization Mitigation</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              The assistant is explicitly identified as an "AI Customer Support Assistant". It rejects synthetic human personas, fake profile photographs, personal feelings, or human claims, fostering appropriate cognitive distance.
            </p>
          </div>

          {/* Pillar 3 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">3. Source Attribution & Grounding</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Every factual assertion cites its source document, page number, and chunk. Customers can click "View Source" to examine the raw policy excerpt that justified the response.
            </p>
          </div>

          {/* Pillar 4 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">4. Uncertainty Communication & Safe Refusal</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Rather than feigning confidence, answers are calibrated as High, Moderate, Low, or "Unable to determine". When documentation is insufficient, the system safely refuses rather than fabricating policies.
            </p>
          </div>
        </div>
      </div>

      {/* User Study & Behavioral Research Section */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-purple-50 text-purple-700 rounded-xl">
            <FlaskConical className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-bold text-base text-slate-900">User Study Testing Module</h2>
            <p className="text-xs text-slate-500">Measuring whether users can catch injected AI errors</p>
          </div>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          In real-world deployments, users often skim past inaccurate AI statements when an answer sounds confident. Our built-in User Study presents participants with controlled scenarios—some factually accurate, some containing intentionally injected errors (e.g. claiming a 30-day refund window when policy mandates 7 days).
        </p>

        <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-200/80 text-xs text-purple-900 font-mono space-y-1">
          <p className="font-semibold text-purple-950 uppercase text-[11px] tracking-wider">
            Primary Research Metric:
          </p>
          <p className="text-xs font-bold text-purple-800">
            Error Catch Rate (%) = (Correctly Detected Injected Errors / Total Injected-Error Scenarios) × 100
          </p>
        </div>
      </div>

      {/* System Architecture */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="font-bold text-base text-slate-900 flex items-center space-x-2">
          <Database className="w-5 h-5 text-blue-600" />
          <span>System Architecture & Pipeline</span>
        </h2>
        <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="font-bold text-slate-800">1. Document Processing:</span> Supports PDF, TXT, and DOCX. Extracts readable pages and creates structured text chunks retaining document name, page, and chunk ID.
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="font-bold text-slate-800">2. Vector Indexing:</span> High-precision hybrid search vector store with ChromaDB, featuring subword TF-IDF embeddings with zero network requirements and instant cold-start readiness.
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="font-bold text-slate-800">3. Grounded Synthesis & LLM:</span> Pluggable LLM provider (supporting local high-precision grounded synthesis or OpenAI/Gemini through environment variables).
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="font-bold text-slate-800">4. SQLite Relational Layer:</span> Stores users, chat sessions, message logs with confidence scores, feedback submissions, and user study experiment results.
          </div>
        </div>
      </div>
    </div>
  );
};
