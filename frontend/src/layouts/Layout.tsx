import React, { useState } from 'react';
import {
  MessageSquare,
  FileText,
  FlaskConical,
  BarChart3,
  Info,
  ShieldAlert,
  ShieldCheck,
  Bot,
  Menu,
  X,
  Languages
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  language?: 'en' | 'ta';
  onLanguageChange?: (lang: 'en' | 'ta') => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  activeTab,
  setActiveTab,
  language = 'en',
  onLanguageChange
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'chat', label: 'Support Chat', icon: MessageSquare },
    { id: 'documents', label: 'Documents & RAG', icon: FileText },
    { id: 'study', label: 'Safety Lab (A/B)', icon: FlaskConical },
    { id: 'dashboard', label: 'Telemetry', icon: BarChart3 },
    { id: 'risk-register', label: 'Risk Matrix', icon: ShieldCheck },
    { id: 'about', label: 'Architecture', icon: Info },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Assistant Identity */}
          <div
            className="flex items-center space-x-3 cursor-pointer select-none"
            onClick={() => setActiveTab('chat')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-slate-900 tracking-tight text-base sm:text-lg">
                  SafeSupport <span className="text-blue-600">AI</span>
                </span>
                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/60">
                  AI Customer Support Assistant
                </span>
              </div>
              <p className="text-[11px] text-slate-500 hidden sm:block">
                Evidence-Grounded • Bias-Mitigated • De-anthropomorphized
              </p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 shadow-sm border border-blue-200/50'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Controls: Language Selector & Safety Badge */}
          <div className="hidden lg:flex items-center space-x-3">
            {onLanguageChange && (
              <div className="flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-200 text-xs">
                <button
                  type="button"
                  onClick={() => onLanguageChange('en')}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                    language === 'en'
                      ? 'bg-white text-blue-700 shadow-xs font-semibold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  English
                </button>
                <button
                  type="button"
                  onClick={() => onLanguageChange('ta')}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-colors flex items-center gap-1 ${
                    language === 'ta'
                      ? 'bg-white text-blue-700 shadow-xs font-semibold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <span>தமிழ்</span>
                </button>
              </div>
            )}

            <div className="flex items-center space-x-1.5 bg-amber-50 border border-amber-200/70 px-2.5 py-1 rounded-xl text-[11px] text-amber-800 font-medium">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <span>Verify Critical Terms</span>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center space-x-2">
            {onLanguageChange && (
              <button
                onClick={() => onLanguageChange(language === 'en' ? 'ta' : 'en')}
                className="px-2 py-1 bg-slate-100 text-xs font-semibold rounded border border-slate-300"
              >
                {language === 'en' ? 'தமிழ்' : 'EN'}
              </button>
            )}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white px-4 py-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium ${
                    isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col">
        {children}
      </main>

      {/* Minimal Footer */}
      <footer className="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-400">
        <p>
          SafeSupport AI • Grounded Customer Support RAG • Anti-Bias, Anti-Overreliance, Non-Anthropomorphic AI.
        </p>
      </footer>
    </div>
  );
};
