import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  PlusCircle,
  Trash2,
  FileText,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Clock
} from 'lucide-react';
import { api } from '../services/api';
import { ChatMessage, ChatSessionInfo, SourceItem } from '../types';
import { SourceModal } from '../components/SourceModal';
import { FeedbackModal } from '../components/FeedbackModal';

const SUGGESTED_QUESTIONS = [
  "How long do I have to request a refund?",
  "How long does standard shipping take?",
  "What is the warranty period for refurbished units?",
  "Can I cancel my order?",
  "Do you support international returns?",
  "What is the cryptocurrency payment policy?"
];

export const ChatPage: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSessionInfo[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [activeSource, setActiveSource] = useState<SourceItem | null>(null);
  const [feedbackTarget, setFeedbackTarget] = useState<{ sessionId: string; messageId: string } | null>(null);
  const [feedbackSubmittedIds, setFeedbackSubmittedIds] = useState<Record<string, string>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
      if (data.length > 0 && !currentSessionId) {
        selectSession(data[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load sessions:', err);
    }
  };

  const selectSession = async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setIsLoading(true);
    setError(null);
    try {
      const session = await api.getSession(sessionId);
      setMessages(session.messages || []);
    } catch (err: any) {
      setError('Failed to load chat history.');
    } finally {
      setIsLoading(false);
    }
  };

  const startNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
  };

  const deleteCurrentSession = async () => {
    if (!currentSessionId) return;
    try {
      await api.deleteSession(currentSessionId);
      setSessions((prev) => prev.filter((s) => s.id !== currentSessionId));
      startNewChat();
    } catch (err: any) {
      setError('Failed to delete conversation.');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputValue).trim();
    if (!query || isLoading) return;

    setError(null);
    setInputValue('');

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: currentSessionId || 'pending',
      role: 'user',
      content: query,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const aiResponse = await api.sendMessage(query, currentSessionId || undefined);
      
      // Update session if it was a new chat
      if (!currentSessionId && aiResponse.session_id) {
        setCurrentSessionId(aiResponse.session_id);
        loadSessions();
      }

      setMessages((prev) => [...prev, aiResponse]);
    } catch (err: any) {
      setError(err.message || 'Failed to get answer from assistant.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleHelpfulClick = async (sessionId: string, messageId: string) => {
    try {
      await api.submitFeedback({
        session_id: sessionId,
        message_id: messageId,
        feedback_type: 'helpful'
      });
      setFeedbackSubmittedIds((prev) => ({ ...prev, [messageId]: 'helpful' }));
    } catch (err) {
      console.error(err);
    }
  };

  const renderConfidenceBadge = (confidence?: string | null) => {
    switch (confidence) {
      case 'High':
        return (
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Confidence: High</span>
          </div>
        );
      case 'Moderate':
        return (
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
            <span>Confidence: Moderate</span>
          </div>
        );
      case 'Low':
        return (
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200">
            <AlertTriangle className="w-3.5 h-3.5 text-orange-600" />
            <span>Confidence: Low</span>
          </div>
        );
      case 'Unable to determine':
      default:
        return (
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <HelpCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>Confidence: Unable to determine</span>
          </div>
        );
    }
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row gap-6 min-h-[calc(100vh-140px)]">
      {/* Sidebar: Conversation Sessions & Safe AI Banner */}
      <div className="w-full lg:w-72 shrink-0 flex flex-col space-y-4">
        {/* New Chat Button */}
        <button
          onClick={startNewChat}
          className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-md shadow-blue-500/10 transition"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Customer Inquiry</span>
        </button>

        {/* Automation Bias / Safety Mitigation Box */}
        <div className="p-4 bg-amber-50/70 border border-amber-200/80 rounded-2xl text-xs text-amber-900 space-y-2">
          <div className="flex items-center space-x-2 font-semibold text-amber-950">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Automation Bias Warning</span>
          </div>
          <p className="text-[11px] leading-relaxed text-amber-800">
            AI answers may contain errors. Always check the cited sources and company policy before making binding customer decisions.
          </p>
        </div>

        {/* Sessions List */}
        <div className="bg-white rounded-2xl border border-slate-200 p-3 flex-1 flex flex-col shadow-sm">
          <div className="flex items-center justify-between px-2 py-1 mb-2 border-b border-slate-100">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Inquiry History
            </span>
            {currentSessionId && (
              <button
                onClick={deleteCurrentSession}
                className="text-slate-400 hover:text-red-600 p-1 rounded transition"
                title="Delete Current Conversation"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="overflow-y-auto space-y-1 max-h-64 lg:max-h-96 pr-1">
            {sessions.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-6">No previous conversations.</p>
            ) : (
              sessions.map((sess) => {
                const isSelected = sess.id === currentSessionId;
                return (
                  <button
                    key={sess.id}
                    onClick={() => selectSession(sess.id)}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs transition truncate flex items-center justify-between ${
                      isSelected
                        ? 'bg-blue-50 text-blue-700 font-medium border border-blue-200/60'
                        : 'text-slate-600 hover:bg-slate-100/70'
                    }`}
                  >
                    <span className="truncate">{sess.title}</span>
                  </button>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        {/* Chat Area Header */}
        <div className="px-6 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="font-semibold text-sm text-slate-800">
                  AI Customer Support Assistant
                </h2>
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              </div>
              <p className="text-[11px] text-slate-500">
                Grounding against active TechNova company knowledge base
              </p>
            </div>
          </div>
          {currentSessionId && (
            <button
              onClick={startNewChat}
              className="text-xs text-slate-500 hover:text-slate-800 px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 transition"
            >
              Clear Current View
            </button>
          )}
        </div>

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-inner">
                <Bot className="w-7 h-7" />
              </div>
              <h3 className="font-semibold text-slate-800 text-base mb-1">
                AI Customer Support Assistant
              </h3>
              <p className="text-xs text-slate-500 mb-6 leading-relaxed">
                I answer questions directly from company documents with source transparency and uncertainty indicators. Ask a customer question below:
              </p>

              {/* Suggested Questions */}
              <div className="w-full space-y-2">
                <span className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider block mb-1">
                  Sample Inquiries to Test:
                </span>
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(q)}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 text-slate-700 transition flex items-center justify-between group"
                  >
                    <span>{q}</span>
                    <Sparkles className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === 'user';
              const feedbackState = feedbackSubmittedIds[msg.id];

              if (isUser) {
                return (
                  <div key={msg.id} className="flex items-start justify-end space-x-2">
                    <div className="max-w-xl bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-sm text-xs sm:text-sm leading-relaxed">
                      {msg.content}
                    </div>
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  </div>
                );
              }

              return (
                <div key={msg.id} className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center shrink-0 border border-slate-200 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="max-w-2xl w-full bg-slate-50/80 border border-slate-200/80 rounded-2xl rounded-tl-none p-4 sm:p-5 shadow-sm space-y-4">
                    {/* Assistant Header & Confidence Pill */}
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-xs text-slate-800">
                          AI Customer Support Assistant
                        </span>
                        <span className="text-[11px] text-slate-400">• AI-generated response</span>
                      </div>
                      {renderConfidenceBadge(msg.confidence)}
                    </div>

                    {/* Actual Answer Content */}
                    <div className="text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </div>

                    {/* Sources Attribution Panel */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="pt-2 border-t border-slate-200/60 space-y-2">
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                          Retrieved Sources:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {msg.sources.map((s, idx) => (
                            <button
                              key={idx}
                              onClick={() => setActiveSource(s)}
                              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-blue-50 hover:border-blue-300 text-slate-700 text-xs font-medium transition group"
                            >
                              <FileText className="w-3.5 h-3.5 text-blue-500" />
                              <span className="truncate max-w-[180px]">{s.document_name}</span>
                              <span className="text-[11px] text-slate-400">P.{s.page_number}</span>
                              <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-blue-500" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Verification Notice Warning */}
                    {msg.verification_notice && (
                      <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start space-x-2.5">
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <p className="font-semibold text-amber-950 text-[11px] uppercase tracking-wide">
                            Verification Notice
                          </p>
                          <p className="text-amber-900/90 text-xs mt-0.5">
                            {msg.verification_notice}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Feedback & Actions */}
                    <div className="pt-2 flex items-center justify-between text-xs text-slate-500 border-t border-slate-200/50">
                      <span className="text-[11px] text-slate-400">Was this answer helpful?</span>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleHelpfulClick(msg.session_id, msg.id)}
                          disabled={Boolean(feedbackState)}
                          className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg border transition ${
                            feedbackState === 'helpful'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-300 font-medium'
                              : 'border-slate-200 hover:bg-slate-100 text-slate-600'
                          }`}
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                          <span>Helpful</span>
                        </button>
                        <button
                          onClick={() => setFeedbackTarget({ sessionId: msg.session_id, messageId: msg.id })}
                          disabled={Boolean(feedbackState)}
                          className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg border transition ${
                            feedbackState === 'unhelpful'
                              ? 'bg-red-50 text-red-700 border-red-300 font-medium'
                              : 'border-slate-200 hover:bg-slate-100 text-slate-600'
                          }`}
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                          <span>Report Issue</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-start space-x-3 animate-fadeIn">
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200 shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-none p-4 text-xs text-slate-600 space-y-2">
                <div className="flex items-center space-x-2 text-blue-600 font-medium">
                  <div className="flex space-x-1">
                    <span className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce"></span>
                  </div>
                  <span>Searching ChromaDB knowledge base & evaluating confidence...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-white border-t border-slate-200">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask a customer support question (e.g., refund policies, shipping times, warranty)..."
              disabled={isLoading}
              className="flex-1 text-xs sm:text-sm px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50/50"
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs sm:text-sm transition flex items-center space-x-1.5 shadow-sm"
            >
              <span>Send</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
          <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
            <span>Press Enter to send. Clear attribution provided for every response.</span>
            <span className="hidden sm:inline">Identified as AI Customer Support Assistant</span>
          </div>
        </div>
      </div>

      {/* Source Inspection Modal */}
      {activeSource && (
        <SourceModal source={activeSource} onClose={() => setActiveSource(null)} />
      )}

      {/* Detailed Feedback Modal */}
      {feedbackTarget && (
        <FeedbackModal
          sessionId={feedbackTarget.sessionId}
          messageId={feedbackTarget.messageId}
          onClose={() => setFeedbackTarget(null)}
          onSubmitted={() => {
            setFeedbackSubmittedIds((prev) => ({
              ...prev,
              [feedbackTarget.messageId]: 'unhelpful'
            }));
          }}
        />
      )}
    </div>
  );
};
