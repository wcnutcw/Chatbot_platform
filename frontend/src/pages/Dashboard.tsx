import React from 'react';
import DashboardStats from '../components/dashboard/DashboardStats';
import DashboardControls from '../components/dashboard/DashboardControls';

interface DashboardProps {
  aiAssistantEnabled: boolean;
  dbType: string;
  isSessionReady: boolean;
  onToggleAI: (enabled: boolean) => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  aiAssistantEnabled,
  dbType,
  isSessionReady,
  onToggleAI
}) => {
  return (
    <div className="space-y-6">
      <DashboardStats
        aiAssistantEnabled={aiAssistantEnabled}
        dbType={dbType}
        isSessionReady={isSessionReady}
      />
      
      <DashboardControls
        aiAssistantEnabled={aiAssistantEnabled}
        onToggleAI={onToggleAI}
      />
    </div>
  );
};

export default Dashboard;