import React, { useState } from 'react';
import { Layout } from './layouts/Layout';
import { ChatPage } from './pages/ChatPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { UserStudyPage } from './pages/UserStudyPage';
import { DashboardPage } from './pages/DashboardPage';
import { AboutPage } from './pages/AboutPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('chat');

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatPage />;
      case 'documents':
        return <DocumentsPage />;
      case 'study':
        return <UserStudyPage onNavigateToDashboard={() => setActiveTab('dashboard')} />;
      case 'dashboard':
        return <DashboardPage />;
      case 'about':
        return (
          <AboutPage
            onNavigateToChat={() => setActiveTab('chat')}
            onNavigateToStudy={() => setActiveTab('study')}
          />
        );
      default:
        return <ChatPage />;
    }
  };

  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
      {renderContent()}
    </Layout>
  );
};

export default App;
