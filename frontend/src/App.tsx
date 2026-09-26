import React, { useState } from 'react';
import { Layout } from './layouts/Layout';
import { ChatPage } from './pages/ChatPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { UserStudyPage } from './pages/UserStudyPage';
import { DashboardPage } from './pages/DashboardPage';
import { AboutPage } from './pages/AboutPage';
import { RiskRegisterPage } from './pages/RiskRegisterPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('chat');
  const [language, setLanguage] = useState<'en' | 'ta'>('en');

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatPage language={language} onLanguageChange={setLanguage} />;
      case 'documents':
        return <DocumentsPage />;
      case 'study':
        return <UserStudyPage onNavigateToDashboard={() => setActiveTab('dashboard')} />;
      case 'dashboard':
        return <DashboardPage />;
      case 'risk-register':
        return <RiskRegisterPage />;
      case 'about':
        return (
          <AboutPage
            onNavigateToChat={() => setActiveTab('chat')}
            onNavigateToStudy={() => setActiveTab('study')}
          />
        );
      default:
        return <ChatPage language={language} onLanguageChange={setLanguage} />;
    }
  };

  return (
    <Layout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      language={language}
      onLanguageChange={setLanguage}
    >
      {renderContent()}
    </Layout>
  );
};

export default App;
