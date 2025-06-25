import React from 'react';
import { Bot, Database, Server, Zap } from 'lucide-react';

interface DashboardStatsProps {
  aiAssistantEnabled: boolean;
  dbType: string;
  isSessionReady: boolean;
}

const DashboardStats: React.FC<DashboardStatsProps> = ({
  aiAssistantEnabled,
  dbType,
  isSessionReady
}) => {
  const stats = [
    {
      label: 'AI Assistant',
      value: aiAssistantEnabled ? 'Active' : 'Inactive',
      icon: Bot,
      color: aiAssistantEnabled ? 'green' : 'gray'
    },
    {
      label: 'Database',
      value: dbType,
      icon: Database,
      color: 'blue'
    },
    {
      label: 'Session',
      value: isSessionReady ? 'Ready' : 'Inactive',
      icon: Server,
      color: isSessionReady ? 'green' : 'gray'
    },
    {
      label: 'Status',
      value: 'Online',
      icon: Zap,
      color: 'emerald'
    }
  ];

  const getColorClasses = (color: string, active: boolean = true) => {
    const colors = {
      green: active ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400',
      blue: 'bg-blue-100 text-blue-600',
      gray: 'bg-gray-100 text-gray-400',
      emerald: 'bg-emerald-100 text-emerald-600'
    };
    return colors[color as keyof typeof colors] || colors.gray;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat) => {
        const Icon = stat.icon;
        const isActive = stat.color !== 'gray';
        
        return (
          <div key={stat.label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-full ${getColorClasses(stat.color, isActive)}`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DashboardStats;