import React, { useState } from 'react';
import { Key, Database, Mail, Facebook, Eye, EyeOff, Save, CheckCircle } from 'lucide-react';

const EnvironmentConfig: React.FC = () => {
  const [showPasswords, setShowPasswords] = useState<{[key: string]: boolean}>({});
  const [savedConfig, setSavedConfig] = useState(false);
  
  const [config, setConfig] = useState({
    openai_api_key: '',
    mongo_url: 'mongodb://localhost:27017/',
    pinecone_api_key: '',
    pinecone_env: 'us-east-1',
    embedding_model: 'text-embedding-3-small',
    hf_token: '',
    typhoon_api_key: '',
    typhoon_api_url: 'https://api.opentyphoon.ai/v1',
    facebook_access_token: '',
    pathummallm_api: '',
    emotional_url: 'https://api.aiforthai.in.th/emonews/prediction',
    emotional_api_key: '',
    email_admin: '',
    email_pass: ''
  });

  const configGroups = [
    {
      title: 'AI Services',
      icon: Key,
      configs: [
        { key: 'openai_api_key', label: 'OpenAI API Key', type: 'password' },
        { key: 'typhoon_api_key', label: 'Typhoon API Key', type: 'password' },
        { key: 'typhoon_api_url', label: 'Typhoon API URL', type: 'text' },
        { key: 'embedding_model', label: 'Embedding Model', type: 'text' },
        { key: 'hf_token', label: 'Hugging Face Token', type: 'password' },
        { key: 'pathummallm_api', label: 'PathummaLLM API', type: 'password' }
      ]
    },
    {
      title: 'Database',
      icon: Database,
      configs: [
        { key: 'mongo_url', label: 'MongoDB URL', type: 'text' },
        { key: 'pinecone_api_key', label: 'Pinecone API Key', type: 'password' },
        { key: 'pinecone_env', label: 'Pinecone Environment', type: 'text' }
      ]
    },
    {
      title: 'External Services',
      icon: Facebook,
      configs: [
        { key: 'facebook_access_token', label: 'Facebook Access Token', type: 'password' },
        { key: 'emotional_url', label: 'Emotional Analysis URL', type: 'text' },
        { key: 'emotional_api_key', label: 'Emotional API Key', type: 'password' }
      ]
    },
    {
      title: 'Email Configuration',
      icon: Mail,
      configs: [
        { key: 'email_admin', label: 'Admin Email', type: 'email' },
        { key: 'email_pass', label: 'Email Password', type: 'password' }
      ]
    }
  ];

  const togglePasswordVisibility = (key: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleInputChange = (key: string, value: string) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveConfig = async () => {
    try {
      // Simulate saving to backend
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSavedConfig(true);
      setTimeout(() => setSavedConfig(false), 3000);
    } catch (error) {
      console.error('Error saving config:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Environment Variables</h3>
          <p className="text-sm text-gray-500">Configure your API keys and service credentials</p>
        </div>
        <button
          onClick={handleSaveConfig}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <Save className="w-4 h-4" />
          <span>Save Configuration</span>
        </button>
      </div>

      {savedConfig && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-green-700">Configuration saved successfully!</span>
        </div>
      )}

      {configGroups.map((group) => {
        const Icon = group.icon;
        return (
          <div key={group.title} className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Icon className="w-5 h-5 text-gray-600" />
              <h4 className="text-md font-medium text-gray-900">{group.title}</h4>
            </div>
            
            <div className="grid grid-cols-1 gap-4">
              {group.configs.map((item) => (
                <div key={item.key}>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {item.label}
                  </label>
                  <div className="relative">
                    <input
                      type={item.type === 'password' && !showPasswords[item.key] ? 'password' : 'text'}
                      value={config[item.key as keyof typeof config]}
                      onChange={(e) => handleInputChange(item.key, e.target.value)}
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder={`Enter ${item.label.toLowerCase()}`}
                    />
                    {item.type === 'password' && (
                      <button
                        type="button"
                        onClick={() => togglePasswordVisibility(item.key)}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      >
                        {showPasswords[item.key] ? (
                          <EyeOff className="w-4 h-4 text-gray-400" />
                        ) : (
                          <Eye className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-medium text-blue-900 mb-2">Configuration Notes</h5>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Environment variables will be stored in the venv/.env file</li>
          <li>• Make sure to restart your backend services after updating configuration</li>
          <li>• Keep your API keys secure and never share them publicly</li>
          <li>• Test your configuration after saving to ensure services work correctly</li>
        </ul>
      </div>
    </div>
  );
};

export default EnvironmentConfig;