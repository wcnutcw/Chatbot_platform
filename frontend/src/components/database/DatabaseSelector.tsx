import React, { useState, useEffect } from 'react';
import { Database, Server, Plus, Search, CheckCircle, AlertCircle, RefreshCw, Loader2, Upload, File, X } from 'lucide-react';

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
  const [startingSession, setStartingSession] = useState(false);
  const [sessionStarted, setSessionStarted] = useState(false);
  const [buttonPressed, setButtonPressed] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // File upload states
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [dragActive, setDragActive] = useState(false);

  // MongoDB connection and database listing - exactly like app.py
  const connectToMongoDB = async () => {
    if (!mongoUri) return;
    
    setLoading(true);
    setConnectionStatus('connecting');
    setErrorMessage('');
    
    try {
      // Try to connect to MongoDB directly like app.py does
      const response = await fetch('/api/mongodb/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uri: mongoUri })
      });

      if (response.ok) {
        const data = await response.json();
        setDatabases(data.databases || []);
        setConnectionStatus('connected');
      } else {
        // If backend endpoint doesn't exist, try direct connection simulation
        try {
          // Simulate MongoDB connection test like app.py
          const testResponse = await fetch('/api/mongodb/databases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uri: mongoUri })
          });

          if (testResponse.ok) {
            const testData = await testResponse.json();
            setDatabases(testData.databases || []);
            setConnectionStatus('connected');
          } else {
            throw new Error('Cannot connect to MongoDB');
          }
        } catch (directError) {
          setConnectionStatus('error');
          setErrorMessage(`ไม่สามารถเชื่อมต่อกับ MongoDB: ${directError}`);
          setDatabases([]);
        }
      }
    } catch (error) {
      console.error('MongoDB connection error:', error);
      setConnectionStatus('error');
      setErrorMessage(`ไม่สามารถเชื่อมต่อกับ MongoDB: ${error}`);
      setDatabases([]);
    } finally {
      setLoading(false);
    }
  };

  // Get collections for selected database - exactly like app.py
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
        throw new Error('Failed to get collections');
      }
    } catch (error) {
      console.error('Error getting collections:', error);
      setErrorMessage(`เกิดข้อผิดพลาดในการดึงข้อมูล collections: ${error}`);
      setCollections([]);
    } finally {
      setLoading(false);
    }
  };

  // Pinecone connection and index listing - exactly like app.py
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
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to connect to Pinecone');
      }
    } catch (error) {
      console.error('Pinecone connection error:', error);
      setConnectionStatus('error');
      setErrorMessage(`เกิดข้อผิดพลาดในการเชื่อมต่อกับ Pinecone: ${error}`);
      setPineconeIndexes([]);
    } finally {
      setLoading(false);
    }
  };

  // File upload handlers
  const handleDragEnter = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDrop = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    );

    setFiles(prev => [...prev, ...droppedFiles]);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setUploadStatus('idle');

    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));
      formData.append('db_type', dbType);
      
      if (dbType === 'MongoDB') {
        formData.append('db_name', dbName);
        formData.append('collection_name', collectionName);
      } else if (dbType === 'Pinecone') {
        formData.append('index_name', indexName);
        formData.append('namespace', namespace);
      }

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        setUploadStatus('success');
        setFiles([]);
        setSuccessMessage('Files uploaded and processed successfully!');
      } else {
        setUploadStatus('error');
        setErrorMessage('Upload failed. Please try again.');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      setErrorMessage('Upload failed. Please check your connection and try again.');
    } finally {
      setUploading(false);
    }
  };

  // Auto-connect when URI changes for MongoDB - like app.py behavior
  useEffect(() => {
    if (dbType === 'MongoDB' && mongoUri && action !== 'create') {
      const timeoutId = setTimeout(() => {
        connectToMongoDB();
      }, 1000); // Slightly longer delay to avoid too many requests
      return () => clearTimeout(timeoutId);
    }
  }, [mongoUri, dbType, action]);

  // Auto-connect when credentials change for Pinecone - like app.py behavior
  useEffect(() => {
    if (dbType === 'Pinecone' && pineconeApiKey && pineconeEnv && action !== 'create') {
      const timeoutId = setTimeout(() => {
        connectToPinecone();
      }, 1000);
      return () => clearTimeout(timeoutId);
    }
  }, [pineconeApiKey, pineconeEnv, dbType, action]);

  // Get collections when database is selected - like app.py behavior
  useEffect(() => {
    if (dbName && action !== 'create' && dbType === 'MongoDB') {
      getCollections(dbName);
    } else {
      setCollections([]);
    }
  }, [dbName, action, dbType]);

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
    setSuccessMessage('');
    setSessionStarted(false);
    setButtonPressed(false);
    setFiles([]);
    setUploadStatus('idle');
  }, [dbType]);

  // Clear messages after 5 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  useEffect(() => {
    if (errorMessage) {
      const timer = setTimeout(() => setErrorMessage(''), 8000);
      return () => clearTimeout(timer);
    }
  }, [errorMessage]);

  const handleStartSession = async () => {
    // Immediate visual feedback
    setButtonPressed(true);
    setTimeout(() => setButtonPressed(false), 150);

    // Clear previous messages
    setErrorMessage('');
    setSuccessMessage('');
    
    // Validate inputs like app.py
    if (dbType === 'MongoDB') {
      if (action === 'existing' && (!dbName || !collectionName)) {
        setErrorMessage('กรุณาเลือกหรือกรอกชื่อฐานข้อมูลและคอลเลกชั่น MongoDB');
        return;
      }
      if (action === 'create' && (!dbName || !collectionName)) {
        setErrorMessage('กรุณากรอกชื่อฐานข้อมูลและคอลเลกชั่น MongoDB ใหม่');
        return;
      }
    }
    
    if (dbType === 'Pinecone' && (!indexName || !namespace)) {
      setErrorMessage('กรุณาเลือกหรือลองใส่ชื่อ Pinecone index');
      return;
    }

    setStartingSession(true);
    
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
        setSessionStarted(true);
        setSuccessMessage(`เซสชันเริ่มต้น! คุณสามารถถามคำถามได้แล้ว Session ID: ${result.session_id.substring(0, 8)}...`);
      } else {
        const errorData = await response.json();
        setErrorMessage(errorData.error || `ไม่สามารถเริ่มต้นเซสชันได้: ${response.status}`);
      }
    } catch (error) {
      console.error('Error starting session:', error);
      setErrorMessage('เกิดข้อผิดพลาดในการเริ่มต้นเซสชัน กรุณาลองใหม่อีกครั้ง');
    } finally {
      setStartingSession(false);
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

  const isFormValid = () => {
    if (dbType === 'MongoDB') {
      return dbName && collectionName;
    }
    if (dbType === 'Pinecone') {
      return indexName && namespace;
    }
    return false;
  };

  const isButtonDisabled = () => {
    return !isFormValid() || startingSession || loading || sessionStarted;
  };

  const getButtonText = () => {
    if (sessionStarted) return 'เซสชันทำงานอยู่';
    if (startingSession) return 'กำลังเริ่มเซสชัน...';
    if (loading) return 'กำลังเชื่อมต่อ...';
    return 'Start Query Session';
  };

  const getButtonIcon = () => {
    if (sessionStarted) return <CheckCircle className="w-4 h-4" />;
    if (startingSession) return <Loader2 className="w-4 h-4 animate-spin" />;
    if (loading) return <RefreshCw className="w-4 h-4 animate-spin" />;
    return <Server className="w-4 h-4" />;
  };

  const getButtonStyles = () => {
    if (sessionStarted) {
      return 'bg-green-600 text-white cursor-default';
    }
    if (isButtonDisabled()) {
      return 'bg-gray-300 text-gray-500 cursor-not-allowed';
    }
    return 'bg-blue-600 text-white hover:bg-blue-700 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl cursor-pointer';
  };

  // Action options like app.py
  const mongoActionOptions = [
    { value: 'existing', label: 'เลือกข้อมูลที่มีอยู่แล้ว', icon: Search },
    { value: 'create', label: 'สร้างที่จัดเก็บข้อมูลใหม่', icon: Plus },
    { value: 'update', label: 'อัพเดตข้อมูลเพิ่มเติม', icon: CheckCircle }
  ];

  const pineconeActionOptions = [
    { value: 'existing', label: 'เลือกข้อมูลที่มีอยู่แล้ว', icon: Search },
    { value: 'create', label: 'สร้างที่จัดเก็บข้อมูลใหม่', icon: Plus }
  ];

  // Show file upload section
  const showFileUpload = action === 'create' || action === 'update';

  return (
    <div className="space-y-6">
      {/* Database Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          เลือกประเภทฐานข้อมูล
        </label>
        <div className="grid grid-cols-2 gap-4">
          {['MongoDB', 'Pinecone'].map((type) => (
            <button
              key={type}
              onClick={() => setDbType(type)}
              disabled={sessionStarted}
              className={`p-4 rounded-lg border-2 transition-all transform hover:scale-105 ${
                dbType === type
                  ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-md'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700 hover:bg-gray-50'
              } ${sessionStarted ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex items-center space-x-3">
                <Database className="w-5 h-5" />
                <span className="font-medium">{type}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2 animate-fade-in">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-green-700">{successMessage}</span>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-700">{errorMessage}</span>
        </div>
      )}

      {/* MongoDB Configuration */}
      {dbType === 'MongoDB' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="font-medium text-gray-900 flex items-center space-x-2">
            <Server className="w-4 h-4" />
            <span>การตั้งค่า MongoDB</span>
            {getConnectionStatusIcon()}
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              MongoDB Connection URI:
            </label>
            <input
              type="text"
              value={mongoUri}
              onChange={(e) => setMongoUri(e.target.value)}
              disabled={sessionStarted}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="mongodb://localhost:27017"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ต้องการดำเนินการอะไร?
            </label>
            <div className="space-y-2">
              {mongoActionOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <label key={option.value} className="flex items-center space-x-3 cursor-pointer hover:bg-gray-100 p-2 rounded transition-colors">
                    <input
                      type="radio"
                      name="action"
                      value={option.value}
                      checked={action === option.value}
                      onChange={(e) => setAction(e.target.value)}
                      disabled={sessionStarted}
                      className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 disabled:cursor-not-allowed"
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
                {action === 'create' ? 'กรอกชื่อฐานข้อมูล MongoDB ใหม่:' : 'เลือกฐานข้อมูล MongoDB:'}
              </label>
              {action === 'create' ? (
                <input
                  type="text"
                  value={dbName}
                  onChange={(e) => setDbName(e.target.value)}
                  disabled={sessionStarted}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                  placeholder="กรอกชื่อฐานข้อมูลใหม่"
                />
              ) : (
                <select
                  value={dbName}
                  onChange={(e) => setDbName(e.target.value)}
                  disabled={loading || databases.length === 0 || sessionStarted}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {loading ? 'กำลังโหลด...' : databases.length === 0 ? 'ไม่พบฐานข้อมูล' : 'เลือกฐานข้อมูล'}
                  </option>
                  {databases.map((db) => (
                    <option key={db} value={db}>{db}</option>
                  ))}
                </select>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {action === 'create' ? 'กรอกชื่อ Collection MongoDB ใหม่:' : 'เลือก Collection MongoDB:'}
              </label>
              {action === 'create' ? (
                <input
                  type="text"
                  value={collectionName}
                  onChange={(e) => setCollectionName(e.target.value)}
                  disabled={sessionStarted}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                  placeholder="กรอกชื่อ collection ใหม่"
                />
              ) : (
                <select
                  value={collectionName}
                  onChange={(e) => setCollectionName(e.target.value)}
                  disabled={loading || !dbName || collections.length === 0 || sessionStarted}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {loading ? 'กำลังโหลด...' : !dbName ? 'เลือกฐานข้อมูลก่อน' : collections.length === 0 ? 'ไม่พบ collection' : 'เลือก collection'}
                  </option>
                  {collections.map((collection) => (
                    <option key={collection} value={collection}>{collection}</option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {connectionStatus === 'connected' && databases.length > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2 animate-fade-in">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-green-700 text-sm">
                เชื่อมต่อสำเร็จ พบฐานข้อมูล {databases.length} รายการ
              </span>
            </div>
          )}
        </div>
      )}

      {/* Pinecone Configuration */}
      {dbType === 'Pinecone' && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="font-medium text-gray-900 flex items-center space-x-2">
            <Server className="w-4 h-4" />
            <span>การตั้งค่า Pinecone</span>
            {getConnectionStatusIcon()}
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pinecone API Key:
              </label>
              <input
                type="password"
                value={pineconeApiKey}
                onChange={(e) => setPineconeApiKey(e.target.value)}
                disabled={sessionStarted}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="กรอก Pinecone API key"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pinecone Environment:
              </label>
              <input
                type="text"
                value={pineconeEnv}
                onChange={(e) => setPineconeEnv(e.target.value)}
                disabled={sessionStarted}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="us-west1-gcp"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              คุณต้องการสร้าง Pinecone index ใหม่หรือเลือกที่มีอยู่แล้ว?
            </label>
            <div className="space-y-2">
              {pineconeActionOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <label key={option.value} className="flex items-center space-x-3 cursor-pointer hover:bg-gray-100 p-2 rounded transition-colors">
                    <input
                      type="radio"
                      name="pinecone_action"
                      value={option.value}
                      checked={action === option.value}
                      onChange={(e) => setAction(e.target.value)}
                      disabled={sessionStarted}
                      className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 disabled:cursor-not-allowed"
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
                {action === 'create' ? 'ชื่อ Pinecone Index:' : 'เลือก Pinecone Index:'}
              </label>
              {action === 'create' ? (
                <input
                  type="text"
                  value={indexName}
                  onChange={(e) => setIndexName(e.target.value)}
                  disabled={sessionStarted}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                  placeholder="กรอกชื่อ index ใหม่"
                />
              ) : (
                <select
                  value={indexName}
                  onChange={(e) => setIndexName(e.target.value)}
                  disabled={loading || pineconeIndexes.length === 0 || sessionStarted}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">
                    {loading ? 'กำลังโหลด...' : pineconeIndexes.length === 0 ? 'ไม่พบ index' : 'เลือก index'}
                  </option>
                  {pineconeIndexes.map((index) => (
                    <option key={index} value={index}>{index}</option>
                  ))}
                </select>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pinecone Namespace:
              </label>
              <input
                type="text"
                value={namespace}
                onChange={(e) => setNamespace(e.target.value)}
                disabled={sessionStarted}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="default-namespace"
              />
            </div>
          </div>

          {connectionStatus === 'connected' && pineconeIndexes.length > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2 animate-fade-in">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-green-700 text-sm">
                เชื่อมต่อสำเร็จ พบ index {pineconeIndexes.length} รายการ
              </span>
            </div>
          )}
        </div>
      )}

      {/* File Upload Section - Only show when creating new storage or updating */}
      {showFileUpload && (
        <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-medium text-gray-900 flex items-center space-x-2">
            <Upload className="w-4 h-4" />
            <span>อัปโหลดไฟล์</span>
          </h3>

          {/* Upload Area */}
          <div
            onDragEnter={handleDragEnter}
            onDragOver={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-blue-500 bg-blue-100'
                : 'border-gray-300 hover:border-gray-400 bg-white'
            }`}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              อัปโหลดไฟล์
            </h4>
            <p className="text-gray-500 mb-4">
              ลากและวางไฟล์ PDF หรือ Word ที่นี่ หรือคลิกเพื่อเลือกไฟล์
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
              disabled={uploading || sessionStarted}
            />
            <label
              htmlFor="file-upload"
              className={`inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors ${
                uploading || sessionStarted ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <Upload className="w-4 h-4 mr-2" />
              เลือกไฟล์
            </label>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">ไฟล์ที่เลือก ({files.length})</h4>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
                    <div className="flex items-center space-x-3">
                      <File className="w-5 h-5 text-gray-500" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      disabled={uploading}
                      className="p-1 text-gray-400 hover:text-red-500 transition-colors disabled:cursor-not-allowed"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Button */}
          {files.length > 0 && (
            <button
              onClick={handleUpload}
              disabled={uploading || !isFormValid() || sessionStarted}
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>กำลังอัปโหลด...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>อัปโหลดไฟล์</span>
                </>
              )}
            </button>
          )}

          {/* Upload Status Messages */}
          {uploadStatus === 'success' && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-green-700">ไฟล์อัปโหลดสำเร็จ!</span>
            </div>
          )}

          {uploadStatus === 'error' && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <span className="text-red-700">การอัปโหลดล้มเหลว กรุณาลองใหม่อีกครั้ง</span>
            </div>
          )}

          <div className="text-sm text-gray-600 bg-white p-3 rounded-lg border border-gray-200">
            <p className="font-medium mb-1">หมายเหตุ:</p>
            <ul className="text-xs space-y-1">
              <li>• รองรับไฟล์ PDF และ Word (.docx) เท่านั้น</li>
              <li>• ไฟล์จะถูกประมวลผลและจัดเก็บในฐานข้อมูลที่เลือก</li>
              <li>• กรุณาตรวจสอบการตั้งค่าฐานข้อมูลก่อนอัปโหลด</li>
            </ul>
          </div>
        </div>
      )}

      {/* Start Session Button */}
      <button
        onClick={handleStartSession}
        disabled={isButtonDisabled()}
        className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 transform flex items-center justify-center space-x-2 ${getButtonStyles()} ${
          buttonPressed ? 'scale-95' : ''
        }`}
      >
        {getButtonIcon()}
        <span>{getButtonText()}</span>
      </button>

      {/* Form Validation Helper */}
      {!isFormValid() && !startingSession && !sessionStarted && (
        <div className="text-sm text-gray-500 text-center">
          {dbType === 'MongoDB' 
            ? 'กรุณาเลือกหรือกรอกชื่อฐานข้อมูลและคอลเลกชั่น MongoDB'
            : 'กรุณาเลือกหรือลองใส่ชื่อ Pinecone index'
          }
        </div>
      )}

      {/* Session Active Notice */}
      {sessionStarted && (
        <div className="text-sm text-green-600 text-center font-medium">
          ✅ เซสชันการค้นหาทำงานอยู่และพร้อมใช้งาน
        </div>
      )}
    </div>
  );
};

export default DatabaseSelector;