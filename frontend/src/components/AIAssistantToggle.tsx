import React from 'react';
import { Bot, Power } from 'lucide-react';

interface AIAssistantToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

const AIAssistantToggle: React.FC<AIAssistantToggleProps> = ({ enabled, onToggle }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${enabled ? 'bg-green-100' : 'bg-gray-100'}`}>
            <Bot className={`w-6 h-6 ${enabled ? 'text-green-600' : 'text-gray-400'}`} />
          </div>
          <div>
            <h3 className="font-medium text-gray-900">AI Assistant</h3>
            <p className="text-sm text-gray-500">
              {enabled ? 'Currently active and responding' : 'Currently inactive'}
            </p>
          </div>
        </div>

        <button
          onClick={() => onToggle(!enabled)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
            enabled ? 'bg-green-500' : 'bg-gray-300'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      <div className={`p-4 rounded-lg border ${
        enabled 
          ? 'bg-green-50 border-green-200' 
          : 'bg-gray-50 border-gray-200'
      }`}>
        <div className="flex items-center space-x-2">
          <Power className={`w-4 h-4 ${enabled ? 'text-green-600' : 'text-gray-400'}`} />
          <span className={`text-sm font-medium ${enabled ? 'text-green-700' : 'text-gray-600'}`}>
            Status: {enabled ? 'Active' : 'Inactive'}
          </span>
        </div>
        <p className={`text-xs mt-1 ${enabled ? 'text-green-600' : 'text-gray-500'}`}>
          {enabled 
            ? 'AI Assistant is responding to messages and queries'
            : 'AI Assistant is disabled and not responding'
          }
        </p>
      </div>
    </div>
  );
};

export default AIAssistantToggle;