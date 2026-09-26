import React, { useState } from 'react';
import { X, ThumbsDown, MessageSquare, AlertTriangle, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

interface FeedbackModalProps {
  sessionId: string;
  messageId: string;
  onClose: () => void;
  onSubmitted: () => void;
}

const REASONS = [
  { id: 'incorrect_info', label: 'Incorrect information' },
  { id: 'unsupported_source', label: 'Source does not support answer' },
  { id: 'unclear', label: 'Answer unclear or confusing' },
  { id: 'missing_info', label: 'Missing key company details' },
  { id: 'other', label: 'Other issue' }
];

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  sessionId,
  messageId,
  onClose,
  onSubmitted
}) => {
  const [selectedReason, setSelectedReason] = useState<string>('incorrect_info');
  const [comment, setComment] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await api.submitFeedback({
        session_id: sessionId,
        message_id: messageId,
        feedback_type: 'unhelpful',
        reason: selectedReason,
        comment: comment.trim()
      });
      setSubmitted(true);
      setTimeout(() => {
        onSubmitted();
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Failed to submit feedback.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-slate-800">
            <ThumbsDown className="w-5 h-5 text-amber-500" />
            <h3 className="font-semibold text-base">Report AI Response Issue</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {submitted ? (
          <div className="p-8 text-center flex flex-col items-center">
            <CheckCircle className="w-12 h-12 text-emerald-500 mb-3 animate-bounce" />
            <h4 className="text-lg font-semibold text-slate-800">Feedback Submitted</h4>
            <p className="text-sm text-slate-500 mt-1">
              Thank you for helping us detect inaccuracies and improve AI safety.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <p className="text-xs text-slate-600 leading-relaxed">
              Help us evaluate response quality. Your report helps combat AI hallucinations and automation bias.
            </p>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Reasons List */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                What was the primary issue?
              </label>
              {REASONS.map((r) => (
                <label
                  key={r.id}
                  className={`flex items-center space-x-3 p-2.5 rounded-xl border text-xs cursor-pointer transition ${
                    selectedReason === r.id
                      ? 'border-blue-500 bg-blue-50/60 text-blue-900 font-medium'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="reason"
                    value={r.id}
                    checked={selectedReason === r.id}
                    onChange={(e) => setSelectedReason(e.target.value)}
                    className="text-blue-600 focus:ring-blue-500"
                  />
                  <span>{r.label}</span>
                </label>
              ))}
            </div>

            {/* Additional Comment */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Additional Details (Optional)
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Explain what was incorrect or which source contradicted the response..."
                rows={3}
                className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Actions */}
            <div className="pt-2 flex items-center justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition shadow-sm disabled:opacity-50"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Report'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
