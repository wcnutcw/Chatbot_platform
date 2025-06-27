import React from 'react';
import { Bell, User } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-100">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {/* ✅ Custom RaoBotHub Logo */}
            <div className="flex-shrink-0">
              <img
                src="/image.png"
                alt="RaoBotHub Logo"
                className="w-10 h-10 rounded-lg object-contain"
                onError={(e) => {
                  // Fallback to the second logo if first one fails
                  const target = e.target as HTMLImageElement;
                  if (target.src.includes('image.png')) {
                    target.src = '/71895ade-07e4-4db2-a32a-213fa1a6489e.png';
                  }
                }}
              />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">RaoBotHub</h1>
              <p className="text-sm text-gray-500">แชทบอทที่ตอบโจทย์คนไทย</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              <Bell className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-gray-600" />
              </div>
              <span className="text-sm font-medium text-gray-700">Admin</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;