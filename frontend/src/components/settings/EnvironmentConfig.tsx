import React, { useState, useEffect } from 'react';
import { Key, Database, Mail, Facebook, Eye, EyeOff, Save, CheckCircle, RefreshCw, AlertCircle, Download, Upload, Plus, Trash2, Edit3, Settings, Lock } from 'lucide-react';
import { formatThailandDateTime } from '../../utils/dateUtils';

interface ConfigurationProfile {
  id: string;
  name: string;
  description: string;
  variables: Record<string, string>;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

const EnvironmentConfig: React.FC = () => {
  const [showPasswords, setShowPasswords] = useState<{[key: string]: boolean}>({});
  const [savedConfig, setSavedConfig] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [envInfo, setEnvInfo] = useState<any>(null);
  
  // Configuration management states
  const [configurations, setConfigurations] = useState<ConfigurationProfile[]>([]);
  const [selectedConfigId, setSelectedConfigId] = useState<string>('');
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [newConfigName, setNewConfigName] = useState('');
  const [newConfigDescription, setNewConfigDescription] = useState('');
  
  // Edit mode state - controls whether fields are editable
  const [isEditMode, setIsEditMode] = useState(false);
  
  const [config, setConfig] = useState({
    OPENAI_API_KEY: '',
    MONGO_URL: 'mongodb://localhost:27017/',
    PINECONE_API_KEY: '',
    PINECONE_ENV: 'us-east-1',
    EMBEDDING_MODEL: 'text-embedding-3-small',
    HF_TOKEN: '',
    TYPHOON_API_KEY: '',
    TYPHOON_API_URL: 'https://api.opentyphoon.ai/v1',
    FACEBOOK_ACCESS_TOKEN: '',
    PATHUMMALLM_API: '',
    url_emotional: 'https://api.aiforthai.in.th/emonews/prediction',
    api_key_aiforthai_emotional: '',
    EMAIL_ADMIN: '',
    EMAIL_PASS: ''
  });

  const configGroups = [
    {
      title: 'AI Services',
      icon: Key,
      configs: [
        { key: 'OPENAI_API_KEY', label: 'OpenAI API Key', type: 'password' },
        { key: 'TYPHOON_API_KEY', label: 'Typhoon API Key', type: 'password' },
        { key: 'TYPHOON_API_URL', label: 'Typhoon API URL', type: 'text' },
        { key: 'EMBEDDING_MODEL', label: 'Embedding Model', type: 'text' },
        { key: 'HF_TOKEN', label: 'Hugging Face Token', type: 'password' },
        { key: 'PATHUMMALLM_API', label: 'PathummaLLM API', type: 'password' }
      ]
    },
    {
      title: 'Database',
      icon: Database,
      configs: [
        { key: 'MONGO_URL', label: 'MongoDB URL', type: 'text' },
        { key: 'PINECONE_API_KEY', label: 'Pinecone API Key', type: 'password' },
        { key: 'PINECONE_ENV', label: 'Pinecone Environment', type: 'text' }
      ]
    },
    {
      title: 'External Services',
      icon: Facebook,
      configs: [
        { key: 'FACEBOOK_ACCESS_TOKEN', label: 'Facebook Access Token', type: 'password' },
        { key: 'url_emotional', label: 'Emotional Analysis URL', type: 'text' },
        { key: 'api_key_aiforthai_emotional', label: 'Emotional API Key', type: 'password' }
      ]
    },
    {
      title: 'Email Configuration',
      icon: Mail,
      configs: [
        { key: 'EMAIL_ADMIN', label: 'Admin Email', type: 'email' },
        { key: 'EMAIL_PASS', label: 'Email Password', type: 'password' }
      ]
    }
  ];

  // Load configurations on component mount
  useEffect(() => {
    loadConfigurations();
    loadEnvironmentInfo();
  }, []);

  // Load configuration when selected and exit edit mode
  useEffect(() => {
    if (selectedConfigId) {
      loadSelectedConfiguration();
      setIsEditMode(false); // Exit edit mode when switching configurations
    }
  }, [selectedConfigId]);

  const loadConfigurations = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/environment/configurations');
      if (response.ok) {
        const data = await response.json();
        setConfigurations(data.configurations || []);
        
        // Auto-select active configuration
        const activeConfig = data.configurations?.find((c: ConfigurationProfile) => c.is_active);
        if (activeConfig) {
          setSelectedConfigId(activeConfig.id);
        }
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load configurations');
      }
    } catch (error) {
      console.error('Error loading configurations:', error);
      setError('Network error while loading configurations');
    } finally {
      setLoading(false);
    }
  };

  const loadSelectedConfiguration = async () => {
    if (!selectedConfigId) return;
    
    try {
      const response = await fetch(`/api/environment/configurations/${selectedConfigId}`);
      if (response.ok) {
        const data = await response.json();
        const configData = data.configuration;
        
        // Update config state with loaded variables
        const loadedConfig = { ...config };
        Object.keys(configData.variables || {}).forEach(key => {
          if (key in loadedConfig) {
            loadedConfig[key as keyof typeof config] = configData.variables[key];
          }
        });
        setConfig(loadedConfig);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load configuration');
      }
    } catch (error) {
      console.error('Error loading selected configuration:', error);
      setError('Network error while loading configuration');
    }
  };

  const loadEnvironmentInfo = async () => {
    try {
      const response = await fetch('/api/environment/info');
      if (response.ok) {
        const data = await response.json();
        setEnvInfo(data.info);
      }
    } catch (error) {
      console.error('Error loading environment info:', error);
    }
  };

  const handleCreateNewConfiguration = async () => {
    if (!newConfigName.trim()) {
      setError('Configuration name is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Filter out empty values
      const filteredConfig = Object.fromEntries(
        Object.entries(config).filter(([_, value]) => value.trim() !== '')
      );

      const response = await fetch('/api/environment/configurations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newConfigName.trim(),
          description: newConfigDescription.trim() || `Configuration created at ${formatThailandDateTime(new Date())}`,
          variables: filteredConfig
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSavedConfig(true);
        setTimeout(() => setSavedConfig(false), 3000);
        
        // Reset form
        setIsCreatingNew(false);
        setNewConfigName('');
        setNewConfigDescription('');
        setIsEditMode(false); // Exit edit mode after creating
        
        // Reload configurations and select the new one
        await loadConfigurations();
        setSelectedConfigId(data.configuration.id);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to create configuration');
      }
    } catch (error) {
      console.error('Error creating configuration:', error);
      setError('Network error while creating configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateConfiguration = async () => {
    if (!selectedConfigId) return;

    try {
      setLoading(true);
      setError(null);

      // Filter out empty values
      const filteredConfig = Object.fromEntries(
        Object.entries(config).filter(([_, value]) => value.trim() !== '')
      );

      const response = await fetch(`/api/environment/configurations/${selectedConfigId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          variables: filteredConfig
        })
      });

      if (response.ok) {
        setSavedConfig(true);
        setTimeout(() => setSavedConfig(false), 3000);
        setIsEditMode(false); // Exit edit mode after saving
        await loadConfigurations();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to update configuration');
      }
    } catch (error) {
      console.error('Error updating configuration:', error);
      setError('Network error while updating configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleActivateConfiguration = async (configId: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/environment/configurations/${configId}/activate`, {
        method: 'POST'
      });

      if (response.ok) {
        setSavedConfig(true);
        setTimeout(() => setSavedConfig(false), 3000);
        await loadConfigurations();
        await loadEnvironmentInfo();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to activate configuration');
      }
    } catch (error) {
      console.error('Error activating configuration:', error);
      setError('Network error while activating configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConfiguration = async (configId: string) => {
    if (!window.confirm('Are you sure you want to delete this configuration? This action cannot be undone.')) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/environment/configurations/${configId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSavedConfig(true);
        setTimeout(() => setSavedConfig(false), 3000);
        
        // Reset selection if deleted config was selected
        if (selectedConfigId === configId) {
          setSelectedConfigId('');
          setIsEditMode(false); // Exit edit mode when deleting selected config
          // Reset config to defaults
          setConfig({
            OPENAI_API_KEY: '',
            MONGO_URL: 'mongodb://localhost:27017/',
            PINECONE_API_KEY: '',
            PINECONE_ENV: 'us-east-1',
            EMBEDDING_MODEL: 'text-embedding-3-small',
            HF_TOKEN: '',
            TYPHOON_API_KEY: '',
            TYPHOON_API_URL: 'https://api.opentyphoon.ai/v1',
            FACEBOOK_ACCESS_TOKEN: '',
            PATHUMMALLM_API: '',
            url_emotional: 'https://api.aiforthai.in.th/emonews/prediction',
            api_key_aiforthai_emotional: '',
            EMAIL_ADMIN: '',
            EMAIL_PASS: ''
          });
        }
        
        await loadConfigurations();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to delete configuration');
      }
    } catch (error) {
      console.error('Error deleting configuration:', error);
      setError('Network error while deleting configuration');
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = (key: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleInputChange = (key: string, value: string) => {
    // Only allow changes in edit mode
    if (!isEditMode) return;
    
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Handle edit mode toggle
  const handleEditToggle = () => {
    if (isEditMode) {
      // If currently editing, ask for confirmation to cancel changes
      if (window.confirm('Are you sure you want to cancel your changes?')) {
        setIsEditMode(false);
        // Reload the configuration to discard changes
        loadSelectedConfiguration();
      }
    } else {
      // Enter edit mode
      setIsEditMode(true);
    }
  };

  const selectedConfig = configurations.find(c => c.id === selectedConfigId);
  const activeConfig = configurations.find(c => c.is_active);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Environment Configuration Management</h3>
          <p className="text-sm text-gray-500">Create, manage, and switch between different environment configurations</p>
        </div>
      </div>

      {/* Status Messages */}
      {savedConfig && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-green-700">Configuration saved successfully!</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-700">{error}</span>
          <button 
            onClick={() => setError(null)}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            ×
          </button>
        </div>
      )}

      {/* Configuration Management Section */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-md font-medium text-gray-900 flex items-center space-x-2">
            <Settings className="w-5 h-5" />
            <span>Configuration Profiles</span>
          </h4>
          <button
            onClick={() => setIsCreatingNew(true)}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            <Plus className="w-4 h-4" />
            <span>New Configuration</span>
          </button>
        </div>

        {/* Create New Configuration Form */}
        {isCreatingNew && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h5 className="font-medium text-blue-900 mb-3">Create New Configuration</h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-blue-800 mb-2">
                  Configuration Name *
                </label>
                <input
                  type="text"
                  value={newConfigName}
                  onChange={(e) => setNewConfigName(e.target.value)}
                  className="w-full px-3 py-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Production, Development, Testing"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-800 mb-2">
                  Description
                </label>
                <input
                  type="text"
                  value={newConfigDescription}
                  onChange={(e) => setNewConfigDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Optional description"
                />
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleCreateNewConfiguration}
                disabled={loading || !newConfigName.trim()}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                <span>Create Configuration</span>
              </button>
              <button
                onClick={() => {
                  setIsCreatingNew(false);
                  setNewConfigName('');
                  setNewConfigDescription('');
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Configuration Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Configuration to View/Edit
          </label>
          <select
            value={selectedConfigId}
            onChange={(e) => setSelectedConfigId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a configuration...</option>
            {configurations.map((config) => (
              <option key={config.id} value={config.id}>
                {config.name} {config.is_active ? '(Active)' : ''} - {config.description}
              </option>
            ))}
          </select>
        </div>

        {/* Configuration List */}
        {configurations.length > 0 && (
          <div className="space-y-2">
            <h5 className="font-medium text-gray-900">Saved Configurations</h5>
            {configurations.map((config) => (
              <div
                key={config.id}
                className={`p-3 border rounded-lg ${
                  config.is_active 
                    ? 'border-green-500 bg-green-50' 
                    : selectedConfigId === config.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h6 className="font-medium text-gray-900">{config.name}</h6>
                      {config.is_active && (
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                          Active
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">{config.description}</p>
                    <p className="text-xs text-gray-500">
                      Created: {formatThailandDateTime(config.created_at)} | 
                      Updated: {formatThailandDateTime(config.updated_at)} |
                      Variables: {Object.keys(config.variables).length}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {!config.is_active && (
                      <button
                        onClick={() => handleActivateConfiguration(config.id)}
                        disabled={loading}
                        className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:bg-gray-300 transition-colors"
                      >
                        Activate
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedConfigId(config.id)}
                      className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleDeleteConfiguration(config.id)}
                      disabled={loading || config.is_active}
                      className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:bg-gray-300 transition-colors"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Environment Info */}
      {envInfo && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">Current Environment Status</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-blue-800">Active Configuration:</span>
              <div className="text-blue-700">
                {activeConfig ? (
                  <span className="flex items-center space-x-1">
                    <CheckCircle className="w-3 h-3" />
                    <span>{activeConfig.name}</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1">
                    <AlertCircle className="w-3 h-3" />
                    <span>None</span>
                  </span>
                )}
              </div>
            </div>
            <div>
              <span className="font-medium text-blue-800">.env File:</span>
              <div className="text-blue-700">
                {envInfo.env_file.exists ? (
                  <span className="flex items-center space-x-1">
                    <CheckCircle className="w-3 h-3" />
                    <span>{envInfo.env_file.variables_count} variables</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1">
                    <AlertCircle className="w-3 h-3" />
                    <span>Not found</span>
                  </span>
                )}
              </div>
            </div>
            <div>
              <span className="font-medium text-blue-800">Total Configurations:</span>
              <div className="text-blue-700">
                <span className="flex items-center space-x-1">
                  <Database className="w-3 h-3" />
                  <span>{configurations.length}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Editor */}
      {selectedConfig && (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <h4 className="text-md font-medium text-gray-900">
                {isEditMode ? 'Editing' : 'Viewing'}: {selectedConfig.name}
              </h4>
              {/* Edit mode indicator */}
              {!isEditMode && (
                <span className="flex items-center space-x-1 px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                  <Lock className="w-3 h-3" />
                  <span>Read Only</span>
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {/* Edit/Cancel button */}
              <button
                onClick={handleEditToggle}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  isEditMode 
                    ? 'bg-gray-500 text-white hover:bg-gray-600' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                <Edit3 className="w-4 h-4" />
                <span>{isEditMode ? 'Cancel' : 'Edit'}</span>
              </button>
              
              {/* Save button only shows in edit mode */}
              {isEditMode && (
                <button
                  onClick={handleUpdateConfiguration}
                  disabled={loading}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  <span>Save Changes</span>
                </button>
              )}
            </div>
          </div>

          {/* Configuration Groups */}
          {configGroups.map((group) => {
            const Icon = group.icon;
            return (
              <div key={group.title} className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <Icon className="w-5 h-5 text-gray-600" />
                  <h4 className="text-md font-medium text-gray-900">{group.title}</h4>
                  {/* Group-level edit indicator */}
                  {!isEditMode && (
                    <Lock className="w-4 h-4 text-gray-400" />
                  )}
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
                          disabled={!isEditMode} // Disable input when not in edit mode
                          className={`w-full px-3 py-2 pr-10 border rounded-md focus:outline-none transition-colors ${
                            isEditMode 
                              ? 'border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white' 
                              : 'border-gray-200 bg-gray-50 text-gray-600 cursor-not-allowed'
                          }`}
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
        </>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-medium text-blue-900 mb-2">Configuration Management Notes</h5>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Create multiple named configurations for different environments (Production, Development, Testing)</li>
          <li>• Only one configuration can be active at a time</li>
          <li>• Active configuration is automatically synced to the .env file</li>
          <li>• You cannot delete the currently active configuration</li>
          <li>• All configurations are stored securely in the database</li>
          <li>• Switch between configurations instantly without manual file editing</li>
          <li>• ✅ <strong>Click "Edit" to modify settings, then "Save Changes" to apply them</strong></li>
          <li>• ✅ <strong>Settings are read-only by default to prevent accidental changes</strong></li>
          <li>• 🇹🇭 <strong>All timestamps are displayed in Thailand time (UTC+7)</strong></li>
        </ul>
      </div>
    </div>
  );
};

export default EnvironmentConfig;