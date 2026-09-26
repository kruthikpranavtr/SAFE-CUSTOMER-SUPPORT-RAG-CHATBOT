import React from 'react';
import { X, FileText, CheckCircle2, ShieldAlert, Sparkles, BookOpen } from 'lucide-react';
import { EvidenceItem } from '../types';

interface EvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  evidenceItems: EvidenceItem[];
  confidence?: string | null;
  retrievalScore?: number | null;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  isOpen,
  onClose,
  evidenceItems,
  confidence,
  retrievalScore
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-700 to-indigo-800 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/10 rounded-xl backdrop-blur-md">
              <Sparkles className="w-5 h-5 text-blue-200" />
            </div>
            <div>
              <h3 className="font-semibold text-lg flex items-center gap-2">
                Why this answer?
                <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-white/20 text-blue-100">
                  Evidence Inspector
                </span>
              </h3>
              <p className="text-xs text-blue-200">
                Ground truth citations retrieved by our RAG verification engine
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Confidence & Verification Summary */}
        <div className="bg-slate-50 px-6 py-3.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-slate-500 font-medium">Calibrated Confidence:</span>
            <span className={`font-semibold px-2 py-0.5 rounded-md ${
              confidence === 'High' ? 'bg-emerald-100 text-emerald-800' :
              confidence === 'Moderate' ? 'bg-amber-100 text-amber-800' :
              confidence === 'Low' ? 'bg-orange-100 text-orange-800' :
              'bg-rose-100 text-rose-800'
            }`}>
              {confidence || 'Moderate'}
            </span>
          </div>

          {retrievalScore !== undefined && retrievalScore !== null && (
            <div className="flex items-center space-x-2">
              <span className="text-slate-500 font-medium">Retrieval Match:</span>
              <span className="font-semibold text-slate-800">
                {(retrievalScore * 100).toFixed(1)}%
              </span>
            </div>
          )}

          <div className="text-slate-500">
            {evidenceItems.length} supporting {evidenceItems.length === 1 ? 'excerpt' : 'excerpts'}
          </div>
        </div>

        {/* Content Excerpts List */}
        <div className="p-6 max-h-[60vh] overflow-y-auto space-y-4">
          {evidenceItems.length === 0 ? (
            <div className="text-center py-10">
              <ShieldAlert className="w-10 h-10 text-amber-500 mx-auto mb-2 opacity-80" />
              <p className="text-sm font-medium text-slate-700">No Direct Document Citations</p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                The question did not match official policy records with sufficient similarity, preventing hallucinated assertions.
              </p>
            </div>
          ) : (
            evidenceItems.map((item, index) => (
              <div
                key={index}
                className="bg-slate-50 rounded-xl p-4 border border-slate-200 hover:border-blue-300 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-semibold text-slate-800">
                      {item.document_name}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-medium border border-blue-200">
                      Page {item.page_number}
                    </span>
                  </div>

                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    item.relevance === 'High' ? 'bg-emerald-100 text-emerald-800' :
                    item.relevance === 'Medium' ? 'bg-amber-100 text-amber-800' :
                    'bg-slate-200 text-slate-700'
                  }`}>
                    {item.relevance} Relevance ({(item.similarity_score * 100).toFixed(0)}%)
                  </span>
                </div>

                <blockquote className="text-xs text-slate-700 italic border-l-2 border-blue-400 pl-3 py-1 my-2 bg-white rounded-r">
                  "{item.quote}"
                </blockquote>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 px-6 py-3.5 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1.5 text-slate-600 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Verified Against Indexed Company Policies
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
