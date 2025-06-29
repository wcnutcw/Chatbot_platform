import React from 'react';
import { CheckCircle, AlertCircle, Clock, Database, MessageCircle, Upload } from 'lucide-react';

const StatusIndicator: React.FC = () => {
  const services = [
    { name: 'Database Connection', status: 'online', icon: Database },
    { name: 'Chat Service', status: 'online', icon: MessageCircle },
    { name: 'File Upload', status: 'online', icon: Upload },
    { name: 'Facebook Integration', status: 'pending', icon: MessageCircle },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600';
      case 'offline': return 'text-red-600';
      case 'pending': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return CheckCircle;
      case 'offline': return AlertCircle;
      case 'pending': return Clock;
      default: return AlertCircle;
    }
  };

  return (
    <div className="space-y-3">
      {services.map((service) => {
        const ServiceIcon = service.icon;
        const StatusIcon = getStatusIcon(service.status);
        
        return (
          <div key={service.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <ServiceIcon className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-900">{service.name}</span>
            </div>
            <div className="flex items-center space-x-2">
              <StatusIcon className={`w-4 h-4 ${getStatusColor(service.status)}`} />
              <span className={`text-xs capitalize ${getStatusColor(service.status)}`}>
                {service.status}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatusIndicator;