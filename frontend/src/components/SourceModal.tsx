import React from 'react';
import { X, FileText, CheckCircle2, Copy, BookOpen } from 'lucide-react';
import { SourceItem } from '../types';

interface SourceModalProps {
  source: SourceItem | null;
  onClose: () => void;
}

export const SourceModal: React.FC<SourceModalProps> = ({ source, onClose }) => {
  const [copied, setCopied] = React.useState(false);

  if (!source) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(source.content_snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 text-blue-700 rounded-lg">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 text-base">{source.document_name}</h3>
              <p className="text-xs text-slate-500">
                Page {source.page_number} • Chunk ID: <span className="font-mono text-slate-600">{source.chunk_id}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Confidence & Match Details */}
        <div className="px-6 py-3 bg-blue-50/50 border-b border-blue-100 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2 text-blue-800 font-medium">
            <BookOpen className="w-4 h-4 text-blue-600" />
            <span>Retrieved Company Context Snippet</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-slate-500">Relevance Match:</span>
            <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-semibold font-mono">
              {(source.similarity_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Content Area */}
        <div className="p-6 overflow-y-auto flex-1 font-mono text-xs sm:text-sm text-slate-700 leading-relaxed bg-slate-50/30 whitespace-pre-wrap selection:bg-yellow-200">
          {source.content_snippet}
        </div>

        {/* Verification Warning & Actions */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <p className="text-xs text-slate-500 max-w-sm">
            Verify this excerpt against the official company documentation before taking critical action.
          </p>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleCopy}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 bg-white hover:bg-slate-100 text-xs font-medium transition"
            >
              {copied ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Text</span>
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium hover:bg-blue-700 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
