import React, { useState, useEffect } from 'react';
import { X, UserCheck, Send, CheckCircle, AlertTriangle, MessageSquare } from 'lucide-react';
import { api } from '../services/api';
import { EscalationInfo } from '../types';

interface EscalationModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId?: string;
  userQuestion?: string;
  lastAiAnswer?: string;
  onSuccess?: (info: EscalationInfo) => void;
}

export const EscalationModal: React.FC<EscalationModalProps> = ({
  isOpen,
  onClose,
  sessionId,
  userQuestion = '',
  lastAiAnswer = '',
  onSuccess
}) => {
  const [customerName, setCustomerName] = useState('');
  const [email, setEmail] = useState('');
  const [reason, setReason] = useState('Need human assistance');
  const [question, setQuestion] = useState(userQuestion);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedEscalation, setSubmittedEscalation] = useState<EscalationInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setQuestion(userQuestion);
      setError(null);
      setSubmittedEscalation(null);
    }
  }, [isOpen, userQuestion]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerName.trim() || !email.trim() || !question.trim()) {
      setError('Please fill in your name, email, and question details.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const autoSummary = lastAiAnswer
      ? `Customer Query: "${question}". AI assistant responded with policy citations. Customer requested human handoff under category "${reason}".`
      : `Customer Query: "${question}". Direct human escalation request.`;

    const res = await api.createEscalation({
      session_id: sessionId,
      customer_name: customerName,
      email: email,
      question: question,
      conversation_summary: autoSummary,
      reason: reason
    });

    setSubmittedEscalation(res);
    if (onSuccess) {
      onSuccess(res);
    }
  } catch (err: any) {
    setError(err.message || 'Failed to submit escalation request.');
  } finally {
    setIsSubmitting(false);
  }
};

  const handleResetAndClose = () => {
    setSubmittedEscalation(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-600 to-orange-700 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/10 rounded-xl backdrop-blur-md">
              <UserCheck className="w-5 h-5 text-amber-100" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Human Support Escalation</h3>
              <p className="text-xs text-amber-100">
                Connect with a human customer support specialist
              </p>
            </div>
          </div>
          <button
            onClick={handleResetAndClose}
            className="text-white/70 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {submittedEscalation ? (
          /* Confirmation View */
          <div className="p-6 text-center space-y-4">
            <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <h4 className="font-semibold text-slate-800 text-base">Escalation Ticket Created</h4>
              <p className="text-xs text-slate-500 mt-1">
                A human support representative has received your ticket and conversation summary.
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-left text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Ticket ID:</span>
                <span className="font-mono font-semibold text-slate-800">{submittedEscalation.id.slice(0, 8)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Customer:</span>
                <span className="font-semibold text-slate-800">{submittedEscalation.customer_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Notification:</span>
                <span className="text-slate-800">{submittedEscalation.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Status:</span>
                <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold">
                  {submittedEscalation.status}
                </span>
              </div>
              {submittedEscalation.conversation_summary && (
                <div className="pt-2 border-t border-slate-200">
                  <span className="text-slate-500 font-medium block mb-1">Generated Brief for Agent:</span>
                  <p className="text-slate-600 italic bg-white p-2 rounded border border-slate-100">
                    {submittedEscalation.conversation_summary}
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={handleResetAndClose}
              className="w-full py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-sm font-medium transition-colors"
            >
              Return to Chat
            </button>
          </div>
        ) : (
          /* Submission Form */
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John Doe"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Reason for Human Handoff
              </label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
              >
                <option value="Need human assistance">Need human assistance</option>
                <option value="AI answer seems incorrect">AI answer seems incorrect / contested</option>
                <option value="Information not available">Information not in available policies</option>
                <option value="Billing or return dispute">Billing or return exception request</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Issue Description / Question *
              </label>
              <textarea
                rows={3}
                required
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Describe your inquiry for the human specialist..."
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-[11px] text-slate-500 flex items-start gap-2">
              <MessageSquare className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
              <span>
                An automated conversation brief will be provided to the human agent so you won't need to re-explain your issue.
              </span>
            </div>

            <div className="pt-2 flex items-center justify-end space-x-2">
              <button
                type="button"
                onClick={handleResetAndClose}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-medium bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <span>Submitting...</span>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Submit Escalation</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
