import React, { useState, useEffect } from 'react';
import { Database, Server, Plus, Search, CheckCircle } from 'lucide-react';

interface DatabaseSelectorProps {
  dbType: string;
  setDbType: (type: string) => void;
  onSessionReady: (ready: boolean) => void;
  setSessionId: (id: string | null) => void;
}

const DatabaseSelector: React.FC<DatabaseSelectorProps> = ({ 
  dbType, 
  setDbType, 
  onSessionReady,
  setSessionId 
}) => {
  const [mongoUri, setMongoUri] = useState('mongodb://localhost:27017');
  const [action, setAction] = useState('existing');
  const [dbName, setDbName] = useState('');
  const [collectionName, setCollectionName] = useState('');
  const [pineconeApiKey, setPineconeApiKey] = useState('');
  const [pineconeEnv, setPineconeEnv] = useState('us-west1-gcp');
  const [indexName, setIndexName] = useState('');
  const [namespace, setNamespace] = useState('default-namespace');
  const [databases, setDatabases] = useState<string[]>([]);
  const [collections, setCollections] = useState<string[]>([]);

  const handleStartSession = async () => {
    try {
      const data = new FormData();
      data.append('db_type', dbType);
      
      if (dbType === 'MongoDB') {
        data.append('db_name', dbName);
        data.append('collection_name', collectionName);
      } else if (dbType === 'Pinecone') {
        data.append('index_name', indexName);
        data.append('namespace', namespace);
      }

      const response = await fetch('/api/start_session', {
        method: 'POST',
        body: data
      });

      if (response.ok) {
        const result = await response.json();
        setSessionId(result.session_id);
        onSessionReady(true);
      }
    } catch (error) {
      console.error('Error starting session:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Database Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Database Type
        </label>
        <div className="grid grid-cols-2 gap-4">
          {['MongoDB', 'Pinecone'].map((type) => (
            <button
              key={type}
              onClick={() => setDbType(type)}
              className={`p-4 rounded-lg border-2 transition-all ${
                dbType === type
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Database className="w-5 h-5" />
                <span className="font-medium">{type}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* MongoDB Configuration */}
      {dbType === 'MongoDB' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 flex items-center space-x-2">
            <Server className="w-4 h-4" />
            <span>MongoDB Configuration</span>
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Connection URI
            </label>
            <input
              type="text"
              value={mongoUri}
              onChange={(e) => setMongoUri(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="mongodb://localhost:27017"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Action
            </label>
            <div className="space-y-2">
              {[
                { value: 'existing', label: 'Select existing data', icon: Search },
                { value: 'create', label: 'Create new storage', icon: Plus },
                { value: 'update', label: 'Update additional data', icon: CheckCircle }
              ].map((option) => {
                const Icon = option.icon;
                return (
                  <label key={option.value} className="flex items-center space-x-3">
                    <input
                      type="radio"
                      name="action"
                      value={option.value}
                      checked={action === option.value}
                      onChange={(e) => setAction(e.target.value)}
                      className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    />
                    <Icon className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database Name
              </label>
              <input
                type="text"
                value={dbName}
                onChange={(e) => setDbName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter database name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Collection Name
              </label>
              <input
                type="text"
                value={collectionName}
                onChange={(e) => setCollectionName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter collection name"
              />
            </div>
          </div>
        </div>
      )}

      {/* Pinecone Configuration */}
      {dbType === 'Pinecone' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 flex items-center space-x-2">
            <Server className="w-4 h-4" />
            <span>Pinecone Configuration</span>
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Key
              </label>
              <input
                type="password"
                value={pineconeApiKey}
                onChange={(e) => setPineconeApiKey(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter Pinecone API key"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Environment
              </label>
              <input
                type="text"
                value={pineconeEnv}
                onChange={(e) => setPineconeEnv(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="us-west1-gcp"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Index Name
              </label>
              <input
                type="text"
                value={indexName}
                onChange={(e) => setIndexName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter index name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Namespace
              </label>
              <input
                type="text"
                value={namespace}
                onChange={(e) => setNamespace(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="default-namespace"
              />
            </div>
          </div>
        </div>
      )}

      {/* Start Session Button */}
      <button
        onClick={handleStartSession}
        disabled={!dbName || !collectionName}
        className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
      >
        <Server className="w-4 h-4" />
        <span>Start Query Session</span>
      </button>
    </div>
  );
};

export default DatabaseSelector;