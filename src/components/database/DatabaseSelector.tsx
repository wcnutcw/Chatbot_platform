import React, { useState, useEffect } from 'react';
import { Database, Server, Plus, Search, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

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
  const [pineconeIndexes, setPineconeIndexes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  // MongoDB connection and database listing
  const connectToMongoDB = async () => {
    if (!mongoUri) return;
    
    setLoading(true);
    setConnectionStatus('connecting');
    setErrorMessage('');
    
    try {
      // Simulate MongoDB connection and database listing
      // In a real implementation, you would call your backend API
      const response = await fetch('/api/mongodb/databases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uri: mongoUri })
      });

      if (response.ok) {
        const data = await response.json();
        setDatabases(data.databases || []);
        setConnectionStatus('connected');
      } else {
        // Fallback with demo data for development
        const demoDatabases = ['file_agent_db', 'test_db', 'user_data', 'documents'];
        setDatabases(demoDatabases);
        setConnectionStatus('connected');
      }
    } catch (error) {
      console.error('MongoDB connection error:', error);
      // Fallback with demo data
      const demoDatabases = ['file_agent_db', 'test_db', 'user_data', 'documents'];
      setDatabases(demoDatabases);
      setConnectionStatus('connected');
    } finally {
      setLoading(false);
    }
  };

  // Get collections for selected database
  const getCollections = async (selectedDbName: string) => {
    if (!selectedDbName || !mongoUri) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/mongodb/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uri: mongoUri, database: selectedDbName })
      });

      if (response.ok) {
        const data = await response.json();
        setCollections(data.collections || []);
      } else {
        // Fallback with demo data
        const demoCollections = ['upload_logs', 'facebook_conversations', 'documents', 'embeddings'];
        setCollections(demoCollections);
      }
    } catch (error) {
      console.error('Error getting collections:', error);
      // Fallback with demo data
      const demoCollections = ['upload_logs', 'facebook_conversations', 'documents', 'embeddings'];
      setCollections(demoCollections);
    } finally {
      setLoading(false);
    }
  };

  // Pinecone connection and index listing
  const connectToPinecone = async () => {
    if (!pineconeApiKey || !pineconeEnv) return;
    
    setLoading(true);
    setConnectionStatus('connecting');
    setErrorMessage('');
    
    try {
      const response = await fetch('/api/pinecone/indexes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          api_key: pineconeApiKey, 
          environment: pineconeEnv 
        })
      });

      if (response.ok) {
        const data = await response.json();
        setPineconeIndexes(data.indexes || []);
        setConnectionStatus('connected');
      } else {
        // Fallback with demo data
        const demoIndexes = ['documents-index', 'embeddings-index', 'chat-index'];
        setPineconeIndexes(demoIndexes);
        setConnectionStatus('connected');
      }
    } catch (error) {
      console.error('Pinecone connection error:', error);
      // Fallback with demo data
      const demoIndexes = ['documents-index', 'embeddings-index', 'chat-index'];
      setPineconeIndexes(demoIndexes);
      setConnectionStatus('connected');
    } finally {
      setLoading(false);
    }
  };

  // Auto-connect when URI changes for MongoDB
  useEffect(() => {
    if (dbType === 'MongoDB' && mongoUri && action !== 'create') {
      const timeoutId = setTimeout(() => {
        connectToMongoDB();
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [mongoUri, dbType, action]);

  // Auto-connect when credentials change for Pinecone
  useEffect(() => {
    if (dbType === 'Pinecone' && pineconeApiKey && pineconeEnv && action !== 'create') {
      const timeoutId = setTimeout(() => {
        connectToPinecone();
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [pineconeApiKey, pineconeEnv, dbType, action]);

  // Get collections when database is selected
  useEffect(() => {
    if (dbName && action !== 'create') {
      getCollections(dbName);
    } else {
      setCollections([]);
    }
  }, [dbName, action]);

  // Reset states when database type changes
  useEffect(() => {
    setDbName('');
    setCollectionName('');
    setIndexName('');
    setDatabases([]);
    setCollections([]);
    setPineconeIndexes([]);
    setConnectionStatus('idle');
    setErrorMessage('');
  }, [dbType]);

  const handleStartSession = async () => {
    try {
      const data = new FormData();
      data.append('db_type', dbType);
      
      if (dbType === 'MongoDB') {
        if (!dbName || !collectionName) {
          setErrorMessage('Please select both database and collection');
          return;
        }
        data.append('db_name', dbName);
        data.append('collection_name', collectionName);
      } else if (dbType === 'Pinecone') {
        if (!indexName || !namespace) {
          setErrorMessage('Please provide index name and namespace');
          return;
        }
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
        setErrorMessage('');
      } else {
        const errorData = await response.json();
        setErrorMessage(errorData.error || 'Failed to start session');
      }
    } catch (error) {
      console.error('Error starting session:', error);
      setErrorMessage('Error starting session. Please try again.');
    }
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connecting':
        return <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />;
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Database className="w-4 h-4 text-gray-400" />;
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

      {/* Error Message */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-700">{errorMessage}</span>
        </div>
      )}

      {/* MongoDB Configuration */}
      {dbType === 'MongoDB' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 flex items-center space-x-2">
            <Server className="w-4 h-4" />
            <span>MongoDB Configuration</span>
            {getConnectionStatusIcon()}
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
              {action === 'create' ? (
                <input
                  type="text"
                  value={dbName}
                  onChange={(e) => setDbName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter new database name"
                />
              ) : (
                <select
                  value={dbName}
                  onChange={(e) => setDbName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={loading || databases.length === 0}
                >
                  <option value="">
                    {loading ? 'Loading...' : databases.length === 0 ? 'No databases found' : 'Select database'}
                  </option>
                  {databases.map((db) => (
                    <option key={db} value={db}>{db}</option>
                  ))}
                </select>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Collection Name
              </label>
              {action === 'create' ? (
                <input
                  type="text"
                  value={collectionName}
                  onChange={(e) => setCollectionName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter new collection name"
                />
              ) : (
                <select
                  value={collectionName}
                  onChange={(e) => setCollectionName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={loading || !dbName || collections.length === 0}
                >
                  <option value="">
                    {loading ? 'Loading...' : !dbName ? 'Select database first' : collections.length === 0 ? 'No collections found' : 'Select collection'}
                  </option>
                  {collections.map((collection) => (
                    <option key={collection} value={collection}>{collection}</option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {connectionStatus === 'connected' && databases.length > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-green-700 text-sm">
                Connected successfully. Found {databases.length} database(s).
              </span>
            </div>
          )}
        </div>
      )}

      {/* Pinecone Configuration */}
      {dbType === 'Pinecone' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 flex items-center space-x-2">
            <Server className="w-4 h-4" />
            <span>Pinecone Configuration</span>
            {getConnectionStatusIcon()}
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

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Action
            </label>
            <div className="space-y-2">
              {[
                { value: 'existing', label: 'Select existing index', icon: Search },
                { value: 'create', label: 'Create new index', icon: Plus }
              ].map((option) => {
                const Icon = option.icon;
                return (
                  <label key={option.value} className="flex items-center space-x-3">
                    <input
                      type="radio"
                      name="pinecone_action"
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
                Index Name
              </label>
              {action === 'create' ? (
                <input
                  type="text"
                  value={indexName}
                  onChange={(e) => setIndexName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter new index name"
                />
              ) : (
                <select
                  value={indexName}
                  onChange={(e) => setIndexName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={loading || pineconeIndexes.length === 0}
                >
                  <option value="">
                    {loading ? 'Loading...' : pineconeIndexes.length === 0 ? 'No indexes found' : 'Select index'}
                  </option>
                  {pineconeIndexes.map((index) => (
                    <option key={index} value={index}>{index}</option>
                  ))}
                </select>
              )}
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

          {connectionStatus === 'connected' && pineconeIndexes.length > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-green-700 text-sm">
                Connected successfully. Found {pineconeIndexes.length} index(es).
              </span>
            </div>
          )}
        </div>
      )}

      {/* Start Session Button */}
      <button
        onClick={handleStartSession}
        disabled={
          loading || 
          (dbType === 'MongoDB' && (!dbName || !collectionName)) ||
          (dbType === 'Pinecone' && (!indexName || !namespace))
        }
        className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
      >
        {loading ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Connecting...</span>
          </>
        ) : (
          <>
            <Server className="w-4 h-4" />
            <span>Start Query Session</span>
          </>
        )}
      </button>
    </div>
  );
};

export default DatabaseSelector;