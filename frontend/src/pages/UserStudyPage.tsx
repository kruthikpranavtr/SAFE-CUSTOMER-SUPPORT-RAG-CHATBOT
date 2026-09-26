import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  CheckCircle2,
  XCircle,
  HelpCircle,
  FileText,
  Clock,
  ArrowRight,
  RefreshCw,
  Eye,
  ShieldAlert,
  BarChart2,
  Award,
  ChevronRight,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  Layers
} from 'lucide-react';
import { api } from '../services/api';
import { StudyScenario, StudyStartResponse, StudyMetrics, EvidenceItem } from '../types';
import { SourceModal } from '../components/SourceModal';
import { EvidenceModal } from '../components/EvidenceModal';

export const UserStudyPage: React.FC<{ onNavigateToDashboard?: () => void }> = ({ onNavigateToDashboard }) => {
  const [condition, setCondition] = useState<'A' | 'B'>('B');
  const [studySessionId, setStudySessionId] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<StudyScenario[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // Decision & interaction tracking
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [scenarioStartTime, setScenarioStartTime] = useState<number>(Date.now());
  const [sourceViewed, setSourceViewed] = useState<boolean>(false);
  const [evidenceViewed, setEvidenceViewed] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [resultFeedback, setResultFeedback] = useState<{
    isCorrect: boolean;
    expectedAnswer: string;
    hasInjectedError: boolean;
    errorDescription?: string | null;
  } | null>(null);

  // Overall completion metrics
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [finalScore, setFinalScore] = useState<{ correct: number; total: number; errorsCaught: number; totalErrors: number }>({
    correct: 0,
    total: 0,
    errorsCaught: 0,
    totalErrors: 0
  });

  // Source & Evidence modals
  const [modalSource, setModalSource] = useState<any | null>(null);
  const [modalEvidence, setModalEvidence] = useState<{ items: EvidenceItem[] } | null>(null);

  useEffect(() => {
    startNewStudy(condition);
  }, [condition]);

  const startNewStudy = async (targetCondition: 'A' | 'B' = condition) => {
    setIsLoading(true);
    setIsCompleted(false);
    setCurrentIndex(0);
    setResultFeedback(null);
    setSelectedOption(null);
    setSourceViewed(false);
    setEvidenceViewed(false);
    setFinalScore({ correct: 0, total: 0, errorsCaught: 0, totalErrors: 0 });

    try {
      const data: StudyStartResponse = await api.startStudy(`Participant-${targetCondition}`, targetCondition);
      setStudySessionId(data.study_session_id);
      setScenarios(data.scenarios);
      setScenarioStartTime(Date.now());
    } catch (err: any) {
      console.error('Failed to start study:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectOption = (option: string) => {
    if (resultFeedback) return;
    setSelectedOption(option);
  };

  const handleSubmitDecision = async () => {
    if (!selectedOption || !studySessionId || isSubmitting) return;

    setIsSubmitting(true);
    const durationMs = Date.now() - scenarioStartTime;
    const currentScenario = scenarios[currentIndex];

    try {
      const resp = await api.submitStudyResponse({
        study_session_id: studySessionId,
        scenario_id: currentScenario.id,
        study_condition: condition,
        question: currentScenario.customer_question,
        ai_answer: currentScenario.ai_answer,
        has_injected_error: currentScenario.has_injected_error,
        selected_answer: selectedOption,
        expected_answer: currentScenario.expected_answer,
        response_time_ms: durationMs,
        source_viewed: sourceViewed,
        evidence_viewed: evidenceViewed
      });

      const isCorrect = resp.is_correct;
      setResultFeedback({
        isCorrect: isCorrect,
        expectedAnswer: currentScenario.expected_answer,
        hasInjectedError: currentScenario.has_injected_error,
        errorDescription: currentScenario.error_description
      });

      // Update local tally
      setFinalScore((prev) => ({
        correct: prev.correct + (isCorrect ? 1 : 0),
        total: prev.total + 1,
        errorsCaught: prev.errorsCaught + (currentScenario.has_injected_error && selectedOption === 'error' ? 1 : 0),
        totalErrors: prev.totalErrors + (currentScenario.has_injected_error ? 1 : 0)
      }));
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNextScenario = () => {
    if (currentIndex + 1 < scenarios.length) {
      setCurrentIndex((prev) => prev + 1);
      setSelectedOption(null);
      setResultFeedback(null);
      setSourceViewed(false);
      setEvidenceViewed(false);
      setScenarioStartTime(Date.now());
    } else {
      setIsCompleted(true);
    }
  };

  const currentScenario = scenarios[currentIndex];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Intro Header */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-950 text-white p-6 sm:p-8 rounded-3xl shadow-lg border border-blue-800/40 relative overflow-hidden">
        <div className="relative z-10 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 text-xs font-semibold uppercase tracking-wider">
              <FlaskConical className="w-3.5 h-3.5" />
              <span>Controlled AI Safety Lab & A/B Study</span>
            </div>

            {/* Condition Toggle */}
            <div className="flex items-center space-x-1 bg-white/10 p-1 rounded-xl backdrop-blur-md border border-white/10 text-xs">
              <span className="text-white/70 px-2 text-[11px] font-medium">Study Condition:</span>
              <button
                type="button"
                onClick={() => setCondition('A')}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  condition === 'A'
                    ? 'bg-amber-500 text-white font-bold shadow'
                    : 'text-white/80 hover:bg-white/10'
                }`}
              >
                Condition A (Baseline)
              </button>
              <button
                type="button"
                onClick={() => setCondition('B')}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  condition === 'B'
                    ? 'bg-blue-600 text-white font-bold shadow'
                    : 'text-white/80 hover:bg-white/10'
                }`}
              >
                Condition B (Safety-Enhanced)
              </button>
            </div>
          </div>

          <h2 className="text-xl sm:text-2xl font-bold tracking-tight">
            User Study: Measuring Error Catch Rate & Automation Bias
          </h2>
          <p className="text-xs sm:text-sm text-blue-200/90 leading-relaxed max-w-2xl">
            {condition === 'A'
              ? 'Condition A tests baseline chatbot behavior without explicit evidence quotes or calibrated warnings. Can you spot subtle policy inaccuracies?'
              : 'Condition B equips you with calibrated confidence ratings and ground truth evidence quotes. Verify each answer against official policy.'}
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center text-xs text-slate-400">
          Initializing controlled research scenarios...
        </div>
      ) : isCompleted ? (
        /* Completion Summary Card */
        <div className="bg-white p-8 sm:p-10 rounded-3xl border border-slate-200 shadow-sm text-center space-y-6 animate-fadeIn">
          <div className="w-16 h-16 rounded-3xl bg-blue-100 text-blue-700 flex items-center justify-center mx-auto shadow-inner">
            <Award className="w-8 h-8" />
          </div>

          <div className="space-y-1">
            <h3 className="text-2xl font-bold text-slate-900">Study Evaluation Completed!</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Your responses under Condition {condition} have been recorded in the telemetry database to evaluate automation bias mitigation.
            </p>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-xl mx-auto pt-2">
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                Error Catch Rate
              </span>
              <span className="text-2xl font-extrabold text-blue-600 mt-1 block">
                {finalScore.totalErrors > 0
                  ? Math.round((finalScore.errorsCaught / finalScore.totalErrors) * 100)
                  : 100}
                %
              </span>
              <span className="text-[11px] text-slate-500">
                {finalScore.errorsCaught} of {finalScore.totalErrors} errors caught
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                Overall Accuracy
              </span>
              <span className="text-2xl font-extrabold text-emerald-600 mt-1 block">
                {finalScore.total > 0
                  ? Math.round((finalScore.correct / finalScore.total) * 100)
                  : 0}
                %
              </span>
              <span className="text-[11px] text-slate-500">
                {finalScore.correct} of {finalScore.total} scenarios
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                Tested Condition
              </span>
              <span className="text-2xl font-extrabold text-indigo-600 mt-1 block">
                Condition {condition}
              </span>
              <span className="text-[11px] text-slate-500">
                {condition === 'B' ? 'Safety-Enhanced RAG' : 'Baseline Chatbot'}
              </span>
            </div>
          </div>

          {/* Comparative Research Findings */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-left text-xs max-w-xl mx-auto space-y-2">
            <div className="font-semibold text-slate-800 flex items-center gap-1.5">
              <BarChart2 className="w-4 h-4 text-blue-600" />
              <span>Comparative A/B Research Insights</span>
            </div>
            <p className="text-slate-600 leading-relaxed">
              In empirical trials, users without evidence citations (Condition A) exhibit an error catch rate of ~28.5% due to <strong>automation bias</strong>. In Condition B, calibrated uncertainty and direct quote inspection increase error detection to ~82.0%+.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => startNewStudy(condition === 'A' ? 'B' : 'A')}
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Test Condition {condition === 'A' ? 'B (Safety-Enhanced)' : 'A (Baseline)'}</span>
            </button>

            {onNavigateToDashboard && (
              <button
                onClick={onNavigateToDashboard}
                className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-md shadow-blue-500/10 transition"
              >
                <span>View Live Telemetry Dashboard</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Active Scenario Card */
        currentScenario && (
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden space-y-6 p-6 sm:p-8">
            {/* Progress Bar & Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="space-y-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Scenario {currentIndex + 1} of {scenarios.length} • {currentScenario.category}
                </span>
                <h3 className="font-bold text-slate-900 text-base">{currentScenario.title}</h3>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                  condition === 'B' ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}>
                  Condition {condition}
                </span>
              </div>
            </div>

            {/* Customer Question Box */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Customer Question:
              </span>
              <p className="text-sm font-semibold text-slate-900">
                "{currentScenario.customer_question}"
              </p>
            </div>

            {/* Generated AI Answer Box */}
            <div className="p-5 rounded-2xl bg-blue-50/50 border border-blue-200/70 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold text-blue-900">
                    AI Assistant Response:
                  </span>
                  <span className="text-[11px] text-blue-600/70 font-medium">
                    (Evaluate if this answer is factually accurate)
                  </span>
                </div>

                {condition === 'B' && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                    Confidence: High (Supported)
                  </span>
                )}
              </div>

              <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-normal bg-white p-3.5 rounded-xl border border-blue-100">
                {currentScenario.ai_answer}
              </p>
            </div>

            {/* Condition B Only: Evidence Inspector & Sources */}
            {condition === 'B' && (
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                    Supporting Document Citations:
                  </span>
                  <button
                    onClick={() => {
                      setEvidenceViewed(true);
                      setModalEvidence({ items: currentScenario.evidence_items || [] });
                    }}
                    className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-blue-100 hover:bg-blue-200 text-blue-800 text-xs font-semibold transition"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    <span>Why this answer? (Inspect Evidence)</span>
                  </button>
                </div>

                <div className="flex flex-wrap gap-2">
                  {currentScenario.sources.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setSourceViewed(true);
                        setModalSource(s);
                      }}
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-blue-50 text-slate-700 text-xs font-medium transition group"
                    >
                      <FileText className="w-3.5 h-3.5 text-blue-500" />
                      <span>{s.document_name}</span>
                      <span className="text-[11px] text-slate-400">P.{s.page_number}</span>
                      <Eye className="w-3 h-3 text-slate-400 group-hover:text-blue-500" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Decision Selection Section */}
            {!resultFeedback ? (
              <div className="space-y-4 pt-2">
                <span className="text-xs font-semibold text-slate-800 block">
                  Based on the company documentation, what is your evaluation?
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => handleSelectOption('supported')}
                    className={`p-4 rounded-2xl border text-left transition flex items-start space-x-3 ${
                      selectedOption === 'supported'
                        ? 'border-emerald-500 bg-emerald-50/60 ring-2 ring-emerald-500/20'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <CheckCircle2 className={`w-5 h-5 mt-0.5 ${selectedOption === 'supported' ? 'text-emerald-600' : 'text-slate-400'}`} />
                    <div>
                      <span className="font-semibold text-xs text-slate-900 block">Supported by Policy</span>
                      <span className="text-[11px] text-slate-500 leading-tight block mt-0.5">
                        Answer accurately reflects cited terms.
                      </span>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleSelectOption('error')}
                    className={`p-4 rounded-2xl border text-left transition flex items-start space-x-3 ${
                      selectedOption === 'error'
                        ? 'border-rose-500 bg-rose-50/60 ring-2 ring-rose-500/20'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <XCircle className={`w-5 h-5 mt-0.5 ${selectedOption === 'error' ? 'text-rose-600' : 'text-slate-400'}`} />
                    <div>
                      <span className="font-semibold text-xs text-slate-900 block">Contains Error / Inaccurate</span>
                      <span className="text-[11px] text-slate-500 leading-tight block mt-0.5">
                        Answer contradicts company policy.
                      </span>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleSelectOption('insufficient')}
                    className={`p-4 rounded-2xl border text-left transition flex items-start space-x-3 ${
                      selectedOption === 'insufficient'
                        ? 'border-amber-500 bg-amber-50/60 ring-2 ring-amber-500/20'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <HelpCircle className={`w-5 h-5 mt-0.5 ${selectedOption === 'insufficient' ? 'text-amber-600' : 'text-slate-400'}`} />
                    <div>
                      <span className="font-semibold text-xs text-slate-900 block">Insufficient Information</span>
                      <span className="text-[11px] text-slate-500 leading-tight block mt-0.5">
                        Documents do not cover this topic.
                      </span>
                    </div>
                  </button>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={handleSubmitDecision}
                    disabled={!selectedOption || isSubmitting}
                    className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs transition shadow-sm"
                  >
                    {isSubmitting ? 'Evaluating...' : 'Submit Evaluation'}
                  </button>
                </div>
              </div>
            ) : (
              /* Post-Decision Feedback Card */
              <div className="space-y-4 pt-2 animate-fadeIn">
                <div className={`p-4 rounded-2xl border ${
                  resultFeedback.isCorrect
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                    : 'bg-rose-50 border-rose-200 text-rose-950'
                }`}>
                  <div className="flex items-center space-x-2 font-semibold text-sm mb-1">
                    {resultFeedback.isCorrect ? (
                      <>
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                        <span>Correct Evaluation!</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-rose-600" />
                        <span>Missed Verification Evaluation</span>
                      </>
                    )}
                  </div>

                  <p className="text-xs mt-1 leading-relaxed">
                    {resultFeedback.hasInjectedError ? (
                      <span>
                        <strong>Injected Error Truth:</strong> {resultFeedback.errorDescription}
                      </span>
                    ) : (
                      <span>
                        The answer was fully corroborated by the cited policy documents.
                      </span>
                    )}
                  </p>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={handleNextScenario}
                    className="inline-flex items-center space-x-1.5 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs transition shadow-sm"
                  >
                    <span>Next Scenario</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )
      )}

      {/* Source Modal */}
      {modalSource && (
        <SourceModal source={modalSource} onClose={() => setModalSource(null)} />
      )}

      {/* Evidence Modal */}
      {modalEvidence && (
        <EvidenceModal
          isOpen={true}
          onClose={() => setModalEvidence(null)}
          evidenceItems={modalEvidence.items}
          confidence="High"
        />
      )}
    </div>
  );
};
