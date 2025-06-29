import React from 'react';
import AIAssistantToggle from '../controls/AIAssistantToggle';
import StatusIndicator from '../status/StatusIndicator';

interface DashboardControlsProps {
  aiAssistantEnabled: boolean;
  onToggleAI: (enabled: boolean) => void;
}

const DashboardControls: React.FC<DashboardControlsProps> = ({
  aiAssistantEnabled,
  onToggleAI
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Assistant Control</h3>
        <AIAssistantToggle 
          enabled={aiAssistantEnabled} 
          onToggle={onToggleAI} 
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
        <StatusIndicator />
      </div>
    </div>
  );
};

export default DashboardControls;