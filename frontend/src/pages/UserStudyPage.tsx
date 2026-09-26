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
  ChevronRight
} from 'lucide-react';
import { api } from '../services/api';
import { StudyScenario, StudyStartResponse, StudyMetrics } from '../types';
import { SourceModal } from '../components/SourceModal';

export const UserStudyPage: React.FC<{ onNavigateToDashboard?: () => void }> = ({ onNavigateToDashboard }) => {
  const [studySessionId, setStudySessionId] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<StudyScenario[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // Decision & interaction tracking
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [scenarioStartTime, setScenarioStartTime] = useState<number>(Date.now());
  const [sourceViewed, setSourceViewed] = useState<boolean>(false);
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

  // Source modal
  const [modalSource, setModalSource] = useState<any | null>(null);

  useEffect(() => {
    startNewStudy();
  }, []);

  const startNewStudy = async () => {
    setIsLoading(true);
    setIsCompleted(false);
    setCurrentIndex(0);
    setResultFeedback(null);
    setSelectedOption(null);
    setSourceViewed(false);
    setFinalScore({ correct: 0, total: 0, errorsCaught: 0, totalErrors: 0 });

    try {
      const data: StudyStartResponse = await api.startStudy('Participant');
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
    if (resultFeedback) return; // already submitted
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
        question: currentScenario.customer_question,
        ai_answer: currentScenario.ai_answer,
        has_injected_error: currentScenario.has_injected_error,
        selected_answer: selectedOption,
        expected_answer: currentScenario.expected_answer,
        response_time_ms: durationMs,
        source_viewed: sourceViewed
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
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 text-xs font-semibold uppercase tracking-wider">
            <FlaskConical className="w-3.5 h-3.5" />
            <span>Controlled Behavioral Experiment</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight">
            User Study: Detecting Injected Errors & Automation Bias
          </h2>
          <p className="text-xs sm:text-sm text-blue-200/90 leading-relaxed max-w-2xl">
            You will review AI-generated customer support answers. Some answers contain intentionally injected errors that contradict company policy. Use the cited sources to determine whether each answer is supported.
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
              Your results have been recorded in the research database to evaluate automation bias mitigation.
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
                {Math.round((finalScore.correct / finalScore.total) * 100)}%
              </span>
              <span className="text-[11px] text-slate-500">
                {finalScore.correct} of {finalScore.total} scenarios
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                Status
              </span>
              <span className="text-2xl font-extrabold text-indigo-600 mt-1 block">
                Verified
              </span>
              <span className="text-[11px] text-slate-500">Research recorded</span>
            </div>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={startNewStudy}
              className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retake Study</span>
            </button>
            {onNavigateToDashboard && (
              <button
                onClick={onNavigateToDashboard}
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition shadow-sm"
              >
                <BarChart2 className="w-4 h-4" />
                <span>View Aggregate Admin Dashboard</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Active Scenario Card */
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col space-y-6 p-6 sm:p-8">
          {/* Progress Header */}
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-3">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                Scenario {currentIndex + 1} of {scenarios.length}
              </span>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {currentScenario.category}
              </span>
            </div>
            <div className="w-32 bg-slate-100 h-2 rounded-full overflow-hidden">
              <div
                className="bg-blue-600 h-full transition-all duration-300"
                style={{ width: `${((currentIndex + 1) / scenarios.length) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Question Box */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Customer Question:
            </span>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs sm:text-sm font-medium text-slate-800">
              "{currentScenario.customer_question}"
            </div>
          </div>

          {/* AI Answer Box */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                AI Customer Support Assistant Response:
              </span>
              <span className="text-[11px] text-amber-600 font-medium flex items-center space-x-1">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Verify against cited source below</span>
              </span>
            </div>
            <div className="p-5 rounded-2xl bg-blue-50/40 border border-blue-200/80 text-xs sm:text-sm text-slate-800 leading-relaxed">
              {currentScenario.ai_answer}
            </div>
          </div>

          {/* Sources Section */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Supporting Documentation Cited:
            </span>
            <div className="space-y-2">
              {currentScenario.sources.map((src, i) => (
                <div
                  key={i}
                  className="p-4 rounded-2xl border border-slate-200 bg-slate-50/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-white rounded-lg border border-slate-200 text-blue-600 shadow-2xs">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-800">{src.document_name}</p>
                      <p className="text-[11px] text-slate-500">Page {src.page_number}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setSourceViewed(true);
                      setModalSource(src);
                    }}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium transition self-start sm:self-auto"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Supporting Text</span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Decision Choices */}
          <div className="space-y-3 pt-2">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
              Your Decision: Does the provided source support the AI answer?
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { id: 'supported', label: '1. Answer is supported', desc: 'Factual match with cited policy' },
                { id: 'error', label: '2. Answer contains an error', desc: 'Contradicts or falsifies source' },
                { id: 'insufficient', label: '3. Not enough information', desc: 'Policy lacks sufficient coverage' }
              ].map((opt) => {
                const isSelected = selectedOption === opt.id;
                return (
                  <button
                    key={opt.id}
                    disabled={Boolean(resultFeedback)}
                    onClick={() => handleSelectOption(opt.id)}
                    className={`p-4 rounded-2xl border text-left transition flex flex-col justify-between ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/80 ring-2 ring-blue-500 text-blue-900 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700'
                    } ${resultFeedback ? 'opacity-80 cursor-default' : 'cursor-pointer'}`}
                  >
                    <span className="font-semibold text-xs sm:text-sm">{opt.label}</span>
                    <span className="text-[11px] text-slate-500 mt-1">{opt.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Feedback Card after submission */}
          {resultFeedback && (
            <div
              className={`p-5 rounded-2xl border text-xs sm:text-sm animate-fadeIn space-y-2 ${
                resultFeedback.isCorrect
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : 'bg-rose-50 border-rose-200 text-rose-900'
              }`}
            >
              <div className="flex items-center space-x-2 font-bold">
                {resultFeedback.isCorrect ? (
                  <>
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                    <span>Correct Analysis!</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
                    <span>Incorrect Evaluation</span>
                  </>
                )}
              </div>
              <p className="text-xs leading-relaxed">
                Expected decision: <span className="font-bold uppercase tracking-wider">{resultFeedback.expectedAnswer}</span>.
                {resultFeedback.hasInjectedError && (
                  <span className="block mt-1 font-medium">
                    ⚠️ {resultFeedback.errorDescription}
                  </span>
                )}
              </p>
            </div>
          )}

          {/* Action Row */}
          <div className="pt-2 flex items-center justify-between border-t border-slate-100">
            <span className="text-[11px] text-slate-400">
              Source viewed: {sourceViewed ? 'Yes' : 'Not yet'}
            </span>
            <div>
              {!resultFeedback ? (
                <button
                  onClick={handleSubmitDecision}
                  disabled={!selectedOption || isSubmitting}
                  className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs shadow-sm transition flex items-center space-x-1.5"
                >
                  <span>Submit Decision</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={handleNextScenario}
                  className="px-6 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs shadow-sm transition flex items-center space-x-1.5"
                >
                  <span>
                    {currentIndex + 1 < scenarios.length ? 'Next Scenario' : 'View Study Results'}
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Source Modal */}
      {modalSource && (
        <SourceModal source={modalSource} onClose={() => setModalSource(null)} />
      )}
    </div>
  );
};
