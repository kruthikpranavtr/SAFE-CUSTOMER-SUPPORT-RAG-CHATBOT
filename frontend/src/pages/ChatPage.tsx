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
  Clock,
  UserCheck,
  Languages,
  Copy,
  Check,
  RotateCcw,
  Edit2,
  Search,
  BookOpen,
  Package,
  Truck,
  RotateCcw as ReturnIcon,
  DollarSign,
  Shield
} from 'lucide-react';
import { api } from '../services/api';
import { ChatMessage, ChatSessionInfo, SourceItem, EvidenceItem } from '../types';
import { SourceModal } from '../components/SourceModal';
import { FeedbackModal } from '../components/FeedbackModal';
import { EvidenceModal } from '../components/EvidenceModal';
import { EscalationModal } from '../components/EscalationModal';

const CATEGORY_CARDS = [
  { id: 'orders', label: 'Orders', icon: Package, sample: 'Where is my order #Nova-9876?' },
  { id: 'delivery', label: 'Delivery', icon: Truck, sample: 'How long does standard delivery take?' },
  { id: 'returns', label: 'Returns', icon: ReturnIcon, sample: 'How can I return an item?' },
  { id: 'refunds', label: 'Refunds', icon: DollarSign, sample: 'What is your refund policy window?' },
  { id: 'warranty', label: 'Warranty', icon: Shield, sample: 'What does the 1-year warranty cover?' }
];

const SUGGESTED_QUESTIONS_EN = [
  "What is your refund policy?",
  "How long does standard delivery take?",
  "Can I cancel my order within 60 minutes?",
  "What does the 1-year warranty cover?",
  "What is the status of my order #Nova-9876?",
  "Can I return an item without original packaging?"
];

const SUGGESTED_QUESTIONS_TA = [
  "பணம் திரும்பப் பெறுவதற்கான விதிமுறைகள் என்ன?",
  "டெலிவரி எத்தனை நாட்களில் வரும்?",
  "ஆர்டர் செய்த பிறகு ரத்து செய்ய முடியுமா?",
  "பழைய/புதுப்பிக்கப்பட்ட சாதனங்களுக்கு உத்தரவாதம் உண்டா?",
  "சேதமடைந்த பொருளுக்கு ரீஃபண்ட் கிடைக்குமா?"
];

interface ChatPageProps {
  language?: 'en' | 'ta';
  onLanguageChange?: (lang: 'en' | 'ta') => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({
  language = 'en',
  onLanguageChange
}) => {
  const [sessions, setSessions] = useState<ChatSessionInfo[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentSessionSummary, setCurrentSessionSummary] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSessionIds, setSelectedSessionIds] = useState<Set<string>>(new Set());
  const [isDeletingHistory, setIsDeletingHistory] = useState(false);
  
  // Search & rename state
  const [searchQuery, setSearchQuery] = useState('');
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  // Modals state
  const [activeSource, setActiveSource] = useState<SourceItem | null>(null);
  const [feedbackTarget, setFeedbackTarget] = useState<{ sessionId: string; messageId: string } | null>(null);
  const [feedbackSubmittedIds, setFeedbackSubmittedIds] = useState<Record<string, string>>({});
  const [showSummaryModal, setShowSummaryModal] = useState<boolean>(false);
  
  // Evidence & Escalation modals
  const [evidenceModalData, setEvidenceModalData] = useState<{
    items: EvidenceItem[];
    confidence?: string | null;
    score?: number | null;
  } | null>(null);

  const [escalationData, setEscalationData] = useState<{
    userQuestion: string;
    lastAiAnswer: string;
  } | null>(null);

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
      setCurrentSessionSummary(session.summary || null);
    } catch (err: any) {
      setError('Failed to load chat history.');
    } finally {
      setIsLoading(false);
    }
  };

  const startNewChat = () => {
    setCurrentSessionId(null);
    setCurrentSessionSummary(null);
    setMessages([]);
    setError(null);
  };

  const toggleSelectSession = (sessionId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setSelectedSessionIds((prev) => {
      const next = new Set(prev);
      if (next.has(sessionId)) {
        next.delete(sessionId);
      } else {
        next.add(sessionId);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedSessionIds.size === filteredSessions.length) {
      setSelectedSessionIds(new Set());
    } else {
      setSelectedSessionIds(new Set(filteredSessions.map((s) => s.id)));
    }
  };

  const handleStartRename = (s: ChatSessionInfo, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(s.id);
    setEditingTitle(s.title);
  };

  const handleSaveRename = async (sessionId: string, e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.stopPropagation();
    if (!editingTitle.trim()) {
      setEditingSessionId(null);
      return;
    }
    try {
      await api.renameSession(sessionId, editingTitle.trim());
      setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: editingTitle.trim() } : s));
      setEditingSessionId(null);
    } catch (err: any) {
      console.error('Rename failed:', err);
    }
  };

  const deleteSingleSession = async (sessionId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!window.confirm('Delete this conversation from history?')) return;
    try {
      await api.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      setSelectedSessionIds((prev) => {
        const next = new Set(prev);
        next.delete(sessionId);
        return next;
      });
      if (currentSessionId === sessionId) {
        startNewChat();
      }
    } catch (err: any) {
      setError('Failed to delete conversation: ' + (err.message || 'Error'));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedSessionIds.size === 0) return;
    const count = selectedSessionIds.size;
    const confirmMsg = count === 1
      ? 'Delete the selected conversation?'
      : `Are you sure you want to delete ${count} selected conversations?`;
    if (!window.confirm(confirmMsg)) return;

    setIsDeletingHistory(true);
    try {
      await api.bulkDeleteSessions(Array.from(selectedSessionIds));
      setSessions((prev) => prev.filter((s) => !selectedSessionIds.has(s.id)));
      if (currentSessionId && selectedSessionIds.has(currentSessionId)) {
        startNewChat();
      }
      setSelectedSessionIds(new Set());
    } catch (err: any) {
      setError('Failed to delete selected conversations: ' + (err.message || 'Error'));
    } finally {
      setIsDeletingHistory(false);
    }
  };

  const handleClearAllHistory = async () => {
    if (sessions.length === 0) return;
    if (!window.confirm(`Are you sure you want to permanently delete ALL ${sessions.length} conversations? This cannot be undone.`)) return;

    setIsDeletingHistory(true);
    try {
      await api.clearAllSessions();
      setSessions([]);
      setSelectedSessionIds(new Set());
      startNewChat();
    } catch (err: any) {
      setError('Failed to clear chat history: ' + (err.message || 'Error'));
    } finally {
      setIsDeletingHistory(false);
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
      language: language,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const aiResponse = await api.sendMessage(query, currentSessionId || undefined, language);
      
      // Update session if it was a new chat
      if (!currentSessionId && aiResponse.session_id) {
        setCurrentSessionId(aiResponse.session_id);
        loadSessions();
      }

      setMessages((prev) => [...prev, aiResponse]);
    } catch (err: any) {
      setError('I’m having trouble generating a response right now. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!currentSessionId || isRegenerating || isLoading) return;
    setIsRegenerating(true);
    setError(null);
    try {
      const updatedAiMsg = await api.regenerateMessage(currentSessionId, language);
      // Replace last AI message
      setMessages((prev) => {
        const withoutLastAi = [...prev];
        const lastIdx = withoutLastAi.map(m => m.role).lastIndexOf('assistant');
        if (lastIdx !== -1) {
          withoutLastAi[lastIdx] = updatedAiMsg;
          return withoutLastAi;
        }
        return [...prev, updatedAiMsg];
      });
    } catch (err: any) {
      setError('Failed to regenerate response. Please try again.');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleCopyMessage = (text: string, msgId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMessageId(msgId);
    setTimeout(() => {
      setCopiedMessageId(null);
    }, 2000);
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
    const confUpper = (confidence || '').toUpperCase();
    if (confUpper.includes('HIGH')) {
      return (
        <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Evidence Support: HIGH</span>
        </div>
      );
    } else if (confUpper.includes('MEDIUM') || confUpper.includes('MODERATE')) {
      return (
        <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
          <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
          <span>Evidence Support: MEDIUM</span>
        </div>
      );
    } else if (confUpper.includes('LOW')) {
      return (
        <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-orange-50 text-orange-700 border border-orange-200">
          <AlertTriangle className="w-3.5 h-3.5 text-orange-600" />
          <span>Evidence Support: LOW</span>
        </div>
      );
    } else {
      return (
        <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
          <HelpCircle className="w-3.5 h-3.5 text-rose-600" />
          <span>Evidence Support: UNABLE TO DETERMINE</span>
        </div>
      );
    }
  };

  // Group sessions by date
  const filteredSessions = sessions.filter(s => 
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const groupSessions = () => {
    const today = new Date().toDateString();
    const yesterday = new Date(Date.now() - 86400000).toDateString();

    const groups: { today: ChatSessionInfo[]; yesterday: ChatSessionInfo[]; previous: ChatSessionInfo[] } = {
      today: [],
      yesterday: [],
      previous: []
    };

    filteredSessions.forEach(s => {
      const d = new Date(s.updated_at).toDateString();
      if (d === today) {
        groups.today.push(s);
      } else if (d === yesterday) {
        groups.yesterday.push(s);
      } else {
        groups.previous.push(s);
      }
    });

    return groups;
  };

  const grouped = groupSessions();
  const activeQuestions = language === 'ta' ? SUGGESTED_QUESTIONS_TA : SUGGESTED_QUESTIONS_EN;

  return (
    <div className="flex-1 flex flex-col lg:flex-row gap-6 min-h-[calc(100vh-140px)]">
      {/* ===================== SIDEBAR ===================== */}
      <div className="w-full lg:w-72 shrink-0 flex flex-col space-y-4">
        {/* New Chat Button */}
        <button
          onClick={startNewChat}
          className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md shadow-blue-500/10 transition"
        >
          <PlusCircle className="w-4 h-4" />
          <span>+ New Customer Inquiry</span>
        </button>

        {/* Language selector in sidebar */}
        {onLanguageChange && (
          <div className="p-3 bg-white border border-slate-200 rounded-xl flex items-center justify-between text-xs">
            <span className="text-slate-600 font-medium flex items-center gap-1.5">
              <Languages className="w-4 h-4 text-slate-400" /> Language:
            </span>
            <div className="flex gap-1">
              <button
                type="button"
                onClick={() => onLanguageChange('en')}
                className={`px-2.5 py-0.5 rounded font-medium ${
                  language === 'en' ? 'bg-blue-100 text-blue-700 font-bold' : 'text-slate-500 hover:bg-slate-100'
                }`}
              >
                EN
              </button>
              <button
                type="button"
                onClick={() => onLanguageChange('ta')}
                className={`px-2.5 py-0.5 rounded font-medium ${
                  language === 'ta' ? 'bg-blue-100 text-blue-700 font-bold' : 'text-slate-500 hover:bg-slate-100'
                }`}
              >
                தமிழ்
              </button>
            </div>
          </div>
        )}

        {/* Automation Bias / Safety Mitigation Box */}
        <div className="p-3.5 bg-amber-50/70 border border-amber-200/80 rounded-2xl text-xs text-amber-900 space-y-1.5">
          <div className="flex items-center space-x-2 font-semibold text-amber-950">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Automation Bias Warning</span>
          </div>
          <p className="text-[11px] leading-relaxed text-amber-800">
            AI answers may contain errors. Always inspect cited sources before making binding decisions.
          </p>
        </div>

        {/* Sessions List Container */}
        <div className="bg-white rounded-2xl border border-slate-200 p-3 flex-1 flex flex-col shadow-sm">
          {/* Header & Clear All */}
          <div className="flex items-center justify-between px-2 py-1 mb-2 border-b border-slate-100">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Inquiry History {sessions.length > 0 && `(${sessions.length})`}
            </span>
            {sessions.length > 0 && (
              <button
                type="button"
                onClick={handleClearAllHistory}
                disabled={isDeletingHistory}
                className="text-[11px] text-red-500 hover:text-red-700 hover:underline transition font-medium flex items-center gap-1"
                title="Permanently delete all chat history"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clear All</span>
              </button>
            )}
          </div>

          {/* Search Conversations Input */}
          <div className="relative mb-2">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search conversations..."
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Bulk Selection Toolbar */}
          {filteredSessions.length > 0 && (
            <div className="px-2.5 py-1.5 mb-2 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
              <label className="flex items-center space-x-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={filteredSessions.length > 0 && selectedSessionIds.size === filteredSessions.length}
                  onChange={toggleSelectAll}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5 cursor-pointer"
                />
                <span className="text-[11px] text-slate-600 font-medium">
                  {selectedSessionIds.size > 0
                    ? `${selectedSessionIds.size} of ${filteredSessions.length} selected`
                    : 'Select All'}
                </span>
              </label>

              {selectedSessionIds.size > 0 && (
                <button
                  type="button"
                  onClick={handleBulkDelete}
                  disabled={isDeletingHistory}
                  className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-[11px] font-semibold transition shadow-sm"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Delete ({selectedSessionIds.size})</span>
                </button>
              )}
            </div>
          )}

          {/* Date Grouped Sessions */}
          <div className="space-y-3 overflow-y-auto max-h-[340px] pr-1">
            {filteredSessions.length === 0 ? (
              <p className="text-xs text-slate-400 p-2 text-center italic">
                {searchQuery ? 'No matching inquiries found.' : 'No past inquiries found.'}
              </p>
            ) : (
              (['today', 'yesterday', 'previous'] as const).map((groupKey) => {
                const groupList = grouped[groupKey];
                if (groupList.length === 0) return null;
                const groupTitle = groupKey === 'today' ? 'Today' : (groupKey === 'yesterday' ? 'Yesterday' : 'Previous Inquiries');

                return (
                  <div key={groupKey} className="space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2 block">
                      {groupTitle}
                    </span>
                    {groupList.map((s) => {
                      const isSelected = selectedSessionIds.has(s.id);
                      const isCurrent = currentSessionId === s.id;
                      const isEditing = editingSessionId === s.id;

                      return (
                        <div
                          key={s.id}
                          className={`group w-full px-2 py-1.5 rounded-xl text-xs transition flex items-center space-x-2 border ${
                            isCurrent
                              ? 'bg-blue-50 text-blue-700 border-blue-200 font-semibold'
                              : isSelected
                              ? 'bg-slate-100 text-slate-800 border-blue-200'
                              : 'text-slate-600 border-transparent hover:bg-slate-50'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => toggleSelectSession(s.id, e as any)}
                            onClick={(e) => e.stopPropagation()}
                            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5 shrink-0 cursor-pointer"
                          />

                          {isEditing ? (
                            <form 
                              onSubmit={(e) => { e.preventDefault(); handleSaveRename(s.id); }}
                              className="flex-1 flex items-center space-x-1"
                            >
                              <input
                                type="text"
                                value={editingTitle}
                                onChange={(e) => setEditingTitle(e.target.value)}
                                className="flex-1 px-1.5 py-0.5 text-xs rounded border border-blue-300 bg-white"
                                autoFocus
                              />
                              <button
                                type="submit"
                                className="text-emerald-600 hover:text-emerald-800 p-0.5"
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                            </form>
                          ) : (
                            <button
                              type="button"
                              onClick={() => selectSession(s.id)}
                              className="flex-1 text-left flex items-center space-x-1.5 min-w-0"
                            >
                              <Clock className="w-3.5 h-3.5 shrink-0 opacity-50" />
                              <span className="truncate">{s.title || 'Inquiry'}</span>
                            </button>
                          )}

                          {/* Action icons */}
                          {!isEditing && (
                            <div className="flex items-center opacity-0 group-hover:opacity-100 transition space-x-1 shrink-0">
                              <button
                                type="button"
                                onClick={(e) => handleStartRename(s, e)}
                                className="text-slate-400 hover:text-slate-700 p-0.5 rounded"
                                title="Rename inquiry"
                              >
                                <Edit2 className="w-3 h-3" />
                              </button>
                              <button
                                type="button"
                                onClick={(e) => deleteSingleSession(s.id, e)}
                                className="text-slate-400 hover:text-red-600 p-0.5 rounded"
                                title="Delete inquiry"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* ===================== MAIN CHAT DISPLAY ===================== */}
      <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        {/* Chat Header */}
        <div className="px-6 py-3.5 border-b border-slate-200 bg-slate-50/60 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shadow-inner">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="font-bold text-xs sm:text-sm text-slate-800">
                  SafeSupport AI — Customer Assistant
                </h2>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                  Active • Grounded RAG
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Evidence-verified customer support assistant.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Conversation Summary Button if present */}
            {currentSessionSummary && (
              <button
                onClick={() => setShowSummaryModal(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold transition"
                title="View Compact Conversation Summary"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Session Summary</span>
              </button>
            )}

            <button
              onClick={() => {
                const lastUser = [...messages].reverse().find((m) => m.role === 'user');
                const lastAi = [...messages].reverse().find((m) => m.role === 'assistant');
                setEscalationData({
                  userQuestion: lastUser?.content || '',
                  lastAiAnswer: lastAi?.content || ''
                });
              }}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold transition"
            >
              <UserCheck className="w-3.5 h-3.5 text-amber-700" />
              <span>Contact Human Support</span>
            </button>
          </div>
        </div>

        {/* Messages List Area */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.length === 0 ? (
            /* ===================== WELCOME SCREEN (SECTION 45) ===================== */
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto py-8 space-y-6 animate-fadeIn">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Bot className="w-7 h-7" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-slate-900 text-base sm:text-lg">
                  SafeSupport AI — Your Customer Support Assistant
                </h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                  I can answer customer inquiries strictly grounded in verified company policies.
                </p>
              </div>

              {/* Clickable Category Chips */}
              <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
                {CATEGORY_CARDS.map((cat) => {
                  const Icon = cat.icon;
                  return (
                    <button
                      key={cat.id}
                      onClick={() => handleSendMessage(cat.sample)}
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 border border-slate-200 text-slate-700 text-xs font-medium transition"
                    >
                      <Icon className="w-3.5 h-3.5 text-blue-600" />
                      <span>{cat.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Sample Question Buttons */}
              <div className="w-full space-y-2 pt-2 text-left">
                <span className="text-[11px] font-semibold uppercase text-slate-400 tracking-wider block mb-2 text-center">
                  Common Customer Questions:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {activeQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(q)}
                      className="p-3 rounded-xl text-xs border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 text-slate-700 transition flex items-start justify-between group shadow-sm bg-white"
                    >
                      <span className="font-medium text-slate-800 leading-snug">{q}</span>
                      <Sparkles className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 shrink-0 ml-1.5 mt-0.5" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* ===================== CONVERSATION TURNS ===================== */
            messages.map((msg) => {
              const isUser = msg.role === 'user';
              const feedbackState = feedbackSubmittedIds[msg.id];
              const timeStr = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

              if (isUser) {
                return (
                  <div key={msg.id} className="flex items-start justify-end space-x-2 animate-fadeIn">
                    <div className="space-y-1 text-right">
                      <div className="max-w-xl bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-sm text-xs sm:text-sm leading-relaxed text-left">
                        {msg.content}
                      </div>
                      <span className="text-[10px] text-slate-400 block px-1">{timeStr}</span>
                    </div>
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  </div>
                );
              }

              return (
                <div key={msg.id} className="flex items-start space-x-3 animate-fadeIn">
                  <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center shrink-0 border border-slate-200 mt-1 shadow-sm">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="max-w-2xl w-full bg-slate-50/90 border border-slate-200 rounded-2xl rounded-tl-none p-4 sm:p-5 shadow-sm space-y-4">
                    {/* Assistant Header & Confidence Pill */}
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs text-slate-900">
                          AI Customer Support Assistant
                        </span>
                        <span className="text-[10px] text-slate-400">• {timeStr}</span>
                      </div>
                      {renderConfidenceBadge(msg.confidence)}
                    </div>

                    {/* PII Warning Notice if detected */}
                    {msg.pii_warning && (
                      <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-900 flex items-center space-x-2">
                        <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                        <span className="font-medium">{msg.pii_warning}</span>
                      </div>
                    )}

                    {/* Actual Answer Content */}
                    <div className="text-xs sm:text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </div>

                    {/* Action Confirmation Interactive Box (INFORM -> CONFIRM -> ACT) */}
                    {msg.action_confirmation && (
                      <div className="p-3.5 bg-blue-50/90 border border-blue-200 rounded-xl space-y-2.5">
                        <div className="flex items-center space-x-2 text-blue-950 font-semibold text-xs">
                          <AlertCircle className="w-4 h-4 text-blue-600" />
                          <span>Action Confirmation: {msg.action_confirmation.action_name}</span>
                        </div>
                        <p className="text-xs text-blue-800 leading-relaxed">
                          {msg.action_confirmation.confirmation_prompt}
                        </p>
                        <div className="flex items-center gap-2 pt-1">
                          <button
                            type="button"
                            onClick={() => handleSendMessage("Confirm Order Cancellation")}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition"
                          >
                            Confirm {msg.action_confirmation.action_name}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleSendMessage("Keep my order, do not cancel")}
                            className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-xs font-medium transition"
                          >
                            Go Back
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Human Escalation Alert when Abstention or Low Evidence occurs */}
                    {msg.requires_human && (
                      <div className="p-3 bg-amber-50/90 border border-amber-300/80 rounded-xl flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center space-x-2 text-xs text-amber-900">
                          <UserCheck className="w-4 h-4 text-amber-700 shrink-0" />
                          <span>AI cannot safely verify this question. Would you like to contact human support?</span>
                        </div>
                        <button
                          onClick={() => {
                            const lastUser = [...messages].reverse().find((m) => m.role === 'user');
                            setEscalationData({
                              userQuestion: lastUser?.content || '',
                              lastAiAnswer: msg.content
                            });
                          }}
                          className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shrink-0 transition shadow-sm"
                        >
                          Contact Human Support
                        </button>
                      </div>
                    )}

                    {/* Evidence Inspector Button & Sources Attribution */}
                    {msg.evidence_items && msg.evidence_items.length > 0 && (
                      <div className="pt-2 border-t border-slate-200/60 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                            Ground Truth Evidence:
                          </span>
                          <button
                            onClick={() => setEvidenceModalData({
                              items: msg.evidence_items || [],
                              confidence: msg.confidence,
                              score: msg.retrieval_score
                            })}
                            className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-semibold transition"
                          >
                            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                            <span>View Evidence (Inspector)</span>
                          </button>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          {msg.sources && msg.sources.map((s, idx) => (
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

                    {/* Follow-Up Suggestion Chips (SECTION 46) */}
                    {msg.suggestions && msg.suggestions.length > 0 && (
                      <div className="pt-2 border-t border-slate-200/50 space-y-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                          Suggested Questions:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.suggestions.map((s, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSendMessage(s)}
                              className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-50/80 hover:bg-blue-100 text-blue-700 text-xs font-medium border border-blue-200 transition"
                            >
                              <Sparkles className="w-3 h-3 text-blue-500" />
                              <span>{s}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action Toolbar: Copy, Regenerate, Feedback, Escalate (SECTIONS 42 & 43) */}
                    <div className="pt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 border-t border-slate-200/50">
                      <div className="flex items-center space-x-2">
                        {/* Copy button */}
                        <button
                          type="button"
                          onClick={() => handleCopyMessage(msg.content, msg.id)}
                          className="inline-flex items-center space-x-1 px-2 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 transition"
                          title="Copy response to clipboard"
                        >
                          {copiedMessageId === msg.id ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-600" />
                              <span className="text-emerald-700 font-semibold">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>

                        {/* Regenerate button */}
                        <button
                          type="button"
                          onClick={handleRegenerate}
                          disabled={isRegenerating || isLoading}
                          className="inline-flex items-center space-x-1 px-2 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 transition disabled:opacity-50"
                          title="Regenerate with safety guardrails"
                        >
                          <RotateCcw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
                          <span>Regenerate</span>
                        </button>

                        {/* Escalate button */}
                        <button
                          onClick={() => {
                            const lastUser = [...messages].reverse().find((m) => m.role === 'user');
                            setEscalationData({
                              userQuestion: lastUser?.content || '',
                              lastAiAnswer: msg.content
                            });
                          }}
                          className="inline-flex items-center space-x-1 text-slate-600 hover:text-amber-700 font-medium transition px-2 py-1"
                        >
                          <UserCheck className="w-3.5 h-3.5" />
                          <span>Escalate</span>
                        </button>
                      </div>

                      {/* Feedback Buttons */}
                      <div className="flex items-center space-x-2">
                        <span className="text-[11px] text-slate-400">Helpful?</span>
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

          {/* Realistic Typing Indicator (SECTION 41) */}
          {(isLoading || isRegenerating) && (
            <div className="flex items-start space-x-3 animate-fadeIn">
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200 shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-none p-3.5 text-xs text-slate-600 space-y-1">
                <div className="flex items-center space-x-2 text-blue-700 font-medium">
                  <div className="flex space-x-1">
                    <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></span>
                  </div>
                  <span>SafeSupport AI is retrieving verified policy evidence...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
              <button
                onClick={() => handleSendMessage()}
                className="px-2.5 py-1 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold"
              >
                Retry
              </button>
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
              placeholder={
                language === 'ta'
                  ? 'வாடிக்கையாளர் ஆதரவு கேள்வியைக் கேட்கவும் (எ.கா. பணம் திரும்பப் பெறுதல், ஷிப்பிங்)...'
                  : 'Ask a customer support question (e.g., refund policies, shipping times, warranty)...'
              }
              disabled={isLoading || isRegenerating}
              className="flex-1 text-xs sm:text-sm px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50/50"
            />
            <button
              type="submit"
              disabled={isLoading || isRegenerating || !inputValue.trim()}
              className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-xs sm:text-sm transition flex items-center space-x-1.5 shadow-sm"
            >
              <span>Send</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
          <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
            <span>Press Enter to send. Strictly fact-grounded in company documentation.</span>
            <span className="hidden sm:inline">SafeSupport AI Customer Assistant</span>
          </div>
        </div>
      </div>

      {/* ===================== MODALS ===================== */}

      {/* Source Inspection Modal */}
      {activeSource && (
        <SourceModal source={activeSource} onClose={() => setActiveSource(null)} />
      )}

      {/* Evidence Inspector Modal */}
      {evidenceModalData && (
        <EvidenceModal
          isOpen={true}
          onClose={() => setEvidenceModalData(null)}
          evidenceItems={evidenceModalData.items}
          confidence={evidenceModalData.confidence}
          retrievalScore={evidenceModalData.score}
        />
      )}

      {/* Human Escalation Modal */}
      {escalationData && (
        <EscalationModal
          isOpen={true}
          onClose={() => setEscalationData(null)}
          sessionId={currentSessionId || undefined}
          userQuestion={escalationData.userQuestion}
          lastAiAnswer={escalationData.lastAiAnswer}
        />
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

      {/* Compact Conversation Summary Modal (SECTION 33) */}
      {showSummaryModal && currentSessionSummary && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-sm text-slate-900">Compact Conversation Summary</h3>
              </div>
              <button
                onClick={() => setShowSummaryModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-xs font-mono text-slate-800 leading-relaxed whitespace-pre-wrap">
              {currentSessionSummary}
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowSummaryModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold"
              >
                Close Summary
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
