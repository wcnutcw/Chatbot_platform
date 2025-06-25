import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, AlertCircle, Search, MoreVertical, Circle, CheckCircle2 } from 'lucide-react';

interface ChatInterfaceProps {
  sessionId: string | null;
  isSessionReady: boolean;
  aiAssistantEnabled: boolean;
}

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  emotion?: string;
}

interface Conversation {
  id: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  lastMessage: string;
  lastMessageTime: Date;
  unreadCount: number;
  isRead: boolean;
  messages: Message[];
  isOnline: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  sessionId, 
  isSessionReady, 
  aiAssistantEnabled 
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      userId: 'worawit_kob',
      userName: 'Worawit (kob)',
      userAvatar: '/api/placeholder/40/40',
      lastMessage: 'หวังว่าจากเลยที่ให้ไปโปรดอ่านสักก่อน...',
      lastMessageTime: new Date(Date.now() - 10 * 60 * 1000),
      unreadCount: 0,
      isRead: true,
      isOnline: true,
      messages: [
        {
          id: '1',
          type: 'user',
          content: 'สวัสดีครับ ผมต้องการสอบถามเกี่ยวกับบริการ',
          timestamp: new Date(Date.now() - 30 * 60 * 1000)
        },
        {
          id: '2',
          type: 'bot',
          content: 'สวัสดีครับ ยินดีให้บริการ มีอะไรให้ช่วยเหลือไหมครับ',
          timestamp: new Date(Date.now() - 25 * 60 * 1000)
        }
      ]
    },
    {
      id: '2',
      userId: 'fon_user',
      userName: 'Fon',
      lastMessage: 'สวัสดีค่ะ',
      lastMessageTime: new Date(Date.now() - 2 * 60 * 60 * 1000),
      unreadCount: 0,
      isRead: true,
      isOnline: false,
      messages: [
        {
          id: '3',
          type: 'user',
          content: 'สวัสดีค่ะ',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000)
        }
      ]
    },
    {
      id: '3',
      userId: 'user_3',
      userName: 'นักปั่นจากในตำนาน',
      lastMessage: 'เบ',
      lastMessageTime: new Date(Date.now() - 2 * 60 * 60 * 1000),
      unreadCount: 0,
      isRead: true,
      isOnline: true,
      messages: [
        {
          id: '4',
          type: 'user',
          content: 'เบ',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000)
        }
      ]
    },
    {
      id: '4',
      userId: 'markzzz',
      userName: 'Markzzz(ลำรอง)',
      lastMessage: 'เฮลโหล',
      lastMessageTime: new Date(Date.now() - 2 * 60 * 60 * 1000),
      unreadCount: 0,
      isRead: true,
      isOnline: false,
      messages: [
        {
          id: '5',
          type: 'user',
          content: 'เฮลโหล',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000)
        }
      ]
    },
    {
      id: '5',
      userId: 'pim_tha',
      userName: '⚡ PIM_THA ⚡',
      lastMessage: 'จากข้อมูลที่ปรึกษาปูมี คำถามว่า "สารเรียน...',
      lastMessageTime: new Date(Date.now() - 3 * 60 * 60 * 1000),
      unreadCount: 0,
      isRead: true,
      isOnline: true,
      messages: [
        {
          id: '6',
          type: 'user',
          content: 'จากข้อมูลที่ปรึกษาปูมี คำถามว่า "สารเรียน...',
          timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000)
        }
      ]
    },
    {
      id: '6',
      userId: 'pingnutt',
      userName: 'PingNutt',
      lastMessage: 'สวัสดี',
      lastMessageTime: new Date(Date.now() - 4 * 60 * 60 * 1000),
      unreadCount: 2,
      isRead: false,
      isOnline: false,
      messages: [
        {
          id: '7',
          type: 'user',
          content: 'สวัสดี',
          timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000)
        },
        {
          id: '8',
          type: 'user',
          content: 'มีคำถามอยากสอบถาม',
          timestamp: new Date(Date.now() - 3.5 * 60 * 60 * 1000)
        }
      ]
    }
  ]);

  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(conversations[0]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [selectedConversation?.messages]);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      const diffInMinutes = Math.floor(diffInHours * 60);
      return `${diffInMinutes} น.`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)} ชม.`;
    } else {
      return date.toLocaleDateString('th-TH', { day: '2-digit', month: '2-digit' });
    }
  };

  const handleConversationClick = (conversation: Conversation) => {
    setSelectedConversation(conversation);
    
    // Mark as read
    if (!conversation.isRead) {
      setConversations(prev => 
        prev.map(conv => 
          conv.id === conversation.id 
            ? { ...conv, isRead: true, unreadCount: 0 }
            : conv
        )
      );
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedConversation || !isSessionReady || !aiAssistantEnabled) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    // Add user message to conversation
    setConversations(prev => 
      prev.map(conv => 
        conv.id === selectedConversation.id
          ? {
              ...conv,
              messages: [...conv.messages, userMessage],
              lastMessage: inputMessage,
              lastMessageTime: new Date()
            }
          : conv
      )
    );

    setInputMessage('');
    setIsLoading(true);

    try {
      // Simulate emotion analysis
      const emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'neutral'];
      const randomEmotion = emotions[Math.floor(Math.random() * emotions.length)];

      const response = await fetch(`/api/query?session_id=${sessionId}&question=${encodeURIComponent(inputMessage)}&emotional=${randomEmotion}`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'bot',
          content: result.response,
          timestamp: new Date(),
          emotion: randomEmotion
        };

        setConversations(prev => 
          prev.map(conv => 
            conv.id === selectedConversation.id
              ? {
                  ...conv,
                  messages: [...conv.messages, botMessage],
                  lastMessage: result.response,
                  lastMessageTime: new Date()
                }
              : conv
          )
        );
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'ขออภัย เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง',
        timestamp: new Date()
      };

      setConversations(prev => 
        prev.map(conv => 
          conv.id === selectedConversation.id
            ? {
                ...conv,
                messages: [...conv.messages, errorMessage],
                lastMessage: errorMessage.content,
                lastMessageTime: new Date()
              }
            : conv
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    conv.lastMessage.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isSessionReady) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Session</h3>
          <p className="text-gray-500">
            Please configure your database and start a session to begin chatting.
          </p>
        </div>
      </div>
    );
  }

  if (!aiAssistantEnabled) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">AI Assistant Disabled</h3>
          <p className="text-gray-500">
            Please enable the AI Assistant to start chatting.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* Conversations Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">จัดการสนทนา</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="ค้นหาการสนทนา..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {filteredConversations.map((conversation) => (
            <div
              key={conversation.id}
              onClick={() => handleConversationClick(conversation)}
              className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
                selectedConversation?.id === conversation.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className="relative">
                  <div className="w-12 h-12 bg-gray-300 rounded-full flex items-center justify-center">
                    <User className="w-6 h-6 text-gray-600" />
                  </div>
                  {conversation.isOnline && (
                    <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-white rounded-full"></div>
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className={`font-medium truncate ${
                      conversation.isRead ? 'text-gray-600' : 'text-gray-900'
                    }`}>
                      {conversation.userName}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">
                        {formatTime(conversation.lastMessageTime)}
                      </span>
                      {conversation.isRead ? (
                        <CheckCircle2 className="w-3 h-3 text-gray-400" />
                      ) : (
                        <Circle className="w-3 h-3 text-blue-500" />
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <p className={`text-sm truncate ${
                      conversation.isRead ? 'text-gray-500' : 'text-gray-700 font-medium'
                    }`}>
                      {conversation.lastMessage}
                    </p>
                    {conversation.unreadCount > 0 && (
                      <span className="ml-2 px-2 py-1 bg-blue-500 text-white text-xs rounded-full min-w-[20px] text-center">
                        {conversation.unreadCount}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <>
            {/* Chat Header */}
            <div className="p-4 bg-white border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-gray-600" />
                    </div>
                    {selectedConversation.isOnline && (
                      <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                    )}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{selectedConversation.userName}</h3>
                    <p className="text-sm text-gray-500">
                      {selectedConversation.isOnline ? 'ออนไลน์' : 'ออฟไลน์'}
                    </p>
                  </div>
                </div>
                <button className="p-2 hover:bg-gray-100 rounded-lg">
                  <MoreVertical className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {selectedConversation.messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex items-start space-x-3 ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.type === 'bot' && (
                    <div className="p-2 bg-blue-100 rounded-full">
                      <Bot className="w-4 h-4 text-blue-600" />
                    </div>
                  )}
                  
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white rounded-br-md'
                        : 'bg-gray-100 text-gray-900 rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    <p className={`text-xs mt-2 ${
                      message.type === 'user' ? 'text-blue-200' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString('th-TH', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                      {message.emotion && ` • ${message.emotion}`}
                    </p>
                  </div>

                  {message.type === 'user' && (
                    <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-gray-600" />
                    </div>
                  )}
                </div>
              ))}
              
              {isLoading && (
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-blue-100 rounded-full">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="p-4 bg-white border-t border-gray-200">
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="พิมพ์ข้อความ..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  className="px-6 py-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                >
                  <Send className="w-4 h-4" />
                  <span>ส่ง</span>
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">เลือกการสนทนา</h3>
              <p className="text-gray-500">เลือกการสนทนาจากรายการด้านซ้ายเพื่อเริ่มต้น</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;