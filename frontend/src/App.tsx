import React, { useState, useEffect } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';
import DatabaseSelector from './components/database/DatabaseSelector';
import ChatInterface from './components/chat/ChatInterface';
import EnvironmentConfig from './components/settings/EnvironmentConfig';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [aiAssistantEnabled, setAiAssistantEnabled] = useState(true);
  const [dbType, setDbType] = useState('MongoDB');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSessionReady, setIsSessionReady] = useState(false);

  const handleToggleAI = async (enabled: boolean) => {
    try {
      const response = await fetch('/api/toggle_switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enable: enabled })
      });
      
      if (response.ok) {
        setAiAssistantEnabled(enabled);
      }
    } catch (error) {
      console.error('Error toggling AI assistant:', error);
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard
            aiAssistantEnabled={aiAssistantEnabled}
            dbType={dbType}
            isSessionReady={isSessionReady}
            onToggleAI={handleToggleAI}
          />
        );

      case 'database':
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Database Management</h2>
            <DatabaseSelector 
              dbType={dbType} 
              setDbType={setDbType}
              onSessionReady={setIsSessionReady}
              setSessionId={setSessionId}
            />
          </div>
        );

      case 'chat':
        return (
          <ChatInterface 
            sessionId={sessionId}
            isSessionReady={isSessionReady}
            aiAssistantEnabled={aiAssistantEnabled}
          />
        );

      case 'settings':
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Environment Configuration</h2>
            <EnvironmentConfig />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="flex">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        
        {/* Conditional padding - no padding for chat, normal padding for others */}
        <div className={`flex-1 ${activeTab === 'chat' ? '' : 'p-6'}`}>
          {activeTab === 'chat' ? (
            <div className="bg-white shadow-sm border border-gray-100 h-[calc(100vh-80px)]">
              {renderContent()}
            </div>
          ) : (
            renderContent()
          )}
        </div>
      </div>
    </div>
  );
}

export default App;