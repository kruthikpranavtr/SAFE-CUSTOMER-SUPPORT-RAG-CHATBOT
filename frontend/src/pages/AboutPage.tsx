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
  Sparkles,
  UserCheck,
  Languages,
  ShieldCheck,
  Lock
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
          SafeSupport AI — Evidence-Based Customer Support
        </h1>
        <p className="text-sm sm:text-base text-blue-100/90 leading-relaxed max-w-2xl">
          A full-stack RAG customer support system with uncertainty communication, source attribution, automation-bias mitigation, prompt injection guards, human escalation, and controlled behavioral A/B testing.
        </p>
        <div className="pt-2 flex flex-wrap gap-3">
          <button
            onClick={onNavigateToChat}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md transition"
          >
            <span>Launch Support Chat</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={onNavigateToStudy}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-xs border border-white/20 transition"
          >
            <span>Run A/B Safety Lab</span>
            <FlaskConical className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 6 Core Safety Guardrails */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Core Safety Mechanisms & Guardrails</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Pillar 1 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">1. Automation Bias & Overreliance Mitigation</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Users frequently assume AI is infallible. Our interface counteracts cognitive passivity by issuing prominent verification guidance and displaying evidence quotes so users actively verify policies before taking critical action.
            </p>
          </div>

          {/* Pillar 2 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Bot className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">2. De-anthropomorphized Persona</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Explicitly labeled as "AI Customer Support Assistant". Rejects synthetic human identities, fake employee photos, personal feelings, and simulated empathy to maintain appropriate psychological distance.
            </p>
          </div>

          {/* Pillar 3 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">3. Ground Truth Source Attribution</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Every factual assertion links to its source document, page number, and chunk. The interactive "Why this answer?" Evidence Inspector lets users view the exact raw quote that corroborates the answer.
            </p>
          </div>

          {/* Pillar 4 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">4. Uncertainty Communication & Safe Refusal</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Answers are systematically calibrated as High, Moderate, Low, or "Unable to determine". When documents do not substantiate the user's inquiry, the system safely refuses rather than fabricating false company policies.
            </p>
          </div>

          {/* Pillar 5 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
              <UserCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">5. Human Escalation with Auto-Summarization</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Customers can seamlessly escalate unresolved or complex inquiries to human specialists. The system automatically drafts a conversation summary so the customer does not need to re-explain their problem.
            </p>
          </div>

          {/* Pillar 6 */}
          <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center">
              <Languages className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-sm text-slate-800">6. Multilingual Cross-Lingual RAG</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Bilingual support for English and Tamil (தமிழ்). Tamil inquiries undergo cross-lingual concept expansion against English policy documents and synthesize culturally grounded, cited Tamil answers.
            </p>
          </div>
        </div>
      </div>

      {/* Security Defense & Risk Register Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <Lock className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-slate-800">Prompt Injection Defense (PromptGuard)</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Multi-layer defense against adversarial jailbreaks, system prompt override attempts, and indirect prompt injection through uploaded policy documents via sanitization wrappers and privilege boundaries.
          </p>
        </div>

        <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-slate-800">AI Safety Risk Register Matrix</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Maintains an active governance risk register tracking Automation Bias, Anthropomorphization, Hallucination, and Overreliance, mapping each to mitigation strategies and verifiable test suites.
          </p>
        </div>
      </div>

      {/* System Architecture */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="font-bold text-base text-slate-900 flex items-center space-x-2">
          <Database className="w-5 h-5 text-blue-600" />
          <span>Full-Stack Architecture & Pipeline</span>
        </h2>
        <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="font-bold text-slate-800">1. Document Processing:</span> Multi-format parser supporting PDF, TXT, and DOCX. Extracts structured chunks retaining document name, exact page number, and chunk ID.
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="font-bold text-slate-800">2. Vector Indexing:</span> High-precision hybrid vector store with ChromaDB and BM25 lexical re-ranking, running offline with 0ms cold-start and zero external dependencies.
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="font-bold text-slate-800">3. Grounded Synthesis & LLM:</span> Bilingual grounded response synthesis (English & Tamil) with system prompt protection and strict citation anchoring.
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="font-bold text-slate-800">4. SQLite Relational Layer:</span> Stores users, chat sessions, message logs with calibrated confidence, human escalations, risk register items, and A/B user study responses.
          </div>
        </div>
      </div>
    </div>
  );
};
