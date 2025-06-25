import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, AlertCircle, Search, MoreVertical, Circle, CheckCircle2, RefreshCw } from 'lucide-react';
import ConversationList from './ConversationList';
import ChatArea from './ChatArea';
import { Conversation, Message } from '../../types/chat';

interface ChatInterfaceProps {
  sessionId: string | null;
  isSessionReady: boolean;
  aiAssistantEnabled: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  isSessionReady,
  aiAssistantEnabled
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Store previous conversation list for comparison
  const prevConversationsRef = useRef<Conversation[]>([]);

  const loadFacebookConversations = async () => {
    try {
      setError(null);
      
      // Only load conversations when AI assistant is enabled
      if (!aiAssistantEnabled) {
        setConversations([]);
        setSelectedConversation(null);
        setLoading(false);
        return;
      }

      const response = await fetch('/api/facebook/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const fbConversations = data.conversations || [];

        // Only show conversations that have recent activity (last 24 hours)
        const now = new Date();
        const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

        const processedConversations: Conversation[] = fbConversations
          .filter((conv: any) => {
            const lastMessageTime = new Date(conv.lastMessageTime);
            return lastMessageTime > oneDayAgo;
          })
          .map((conv: any) => ({
            ...conv,
            lastMessageTime: new Date(conv.lastMessageTime),
            messages: conv.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            }))
          }));

        const sorted = processedConversations.sort((a, b) =>
          b.lastMessageTime.getTime() - a.lastMessageTime.getTime()
        );

        const prevConvs = prevConversationsRef.current;
        const newConv = sorted.find(conv =>
          !prevConvs.some(prev => prev.id === conv.id)
        );
        const newerConv = sorted.find(conv => {
          const prev = prevConvs.find(p => p.id === conv.id);
          return prev && conv.lastMessageTime > prev.lastMessageTime;
        });

        setConversations(sorted);

        if ((newConv || newerConv) && (!selectedConversation || selectedConversation.id !== (newConv?.id || newerConv?.id))) {
          const toSelect = newConv || newerConv;
          setSelectedConversation(toSelect || null);

          // Mark as read
          if (toSelect && !toSelect.isRead) {
            setConversations(prev =>
              prev.map(conv =>
                conv.id === toSelect.id
                  ? { ...conv, isRead: true, unreadCount: 0 }
                  : conv
              )
            );
          }
        }

        prevConversationsRef.current = processedConversations;
        setLastRefresh(new Date());
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load conversations');
        setConversations([]);
      }
    } catch (error) {
      console.error('Error loading Facebook conversations:', error);
      setError('Network error while loading conversations');
      setConversations([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFacebookConversations();
  }, [aiAssistantEnabled]);

  useEffect(() => {
    if (!aiAssistantEnabled) return;

    const interval = setInterval(() => {
      loadFacebookConversations();
    }, 3000);

    return () => clearInterval(interval);
  }, [aiAssistantEnabled, conversations]);

  const handleConversationSelect = (conversation: Conversation) => {
    setSelectedConversation(conversation);
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

  const handleConversationUpdate = (conversationId: string, updates: Partial<Conversation>) => {
    setConversations(prev =>
      prev.map(conv =>
        conv.id === conversationId
          ? { ...conv, ...updates }
          : conv
      )
    );
    if (selectedConversation?.id === conversationId) {
      setSelectedConversation(prev => prev ? { ...prev, ...updates } : null);
    }
  };

  const handleConversationDelete = (conversationId: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== conversationId));
    if (selectedConversation?.id === conversationId) {
      const remaining = conversations.filter(conv => conv.id !== conversationId);
      setSelectedConversation(remaining[0] || null);
    }
  };

  const handleDeleteMessage = (messageId: string) => {
    if (!selectedConversation) return;

    const updatedMessages = selectedConversation.messages.filter(msg => msg.id !== messageId);
    const updatedConversation = {
      ...selectedConversation,
      messages: updatedMessages,
      lastMessage: updatedMessages.length > 0 ? updatedMessages[updatedMessages.length - 1].content : 'No messages',
      lastMessageTime: updatedMessages.length > 0 ? updatedMessages[updatedMessages.length - 1].timestamp : new Date()
    };

    setSelectedConversation(updatedConversation);

    setConversations(prev =>
      prev.map(conv =>
        conv.id === selectedConversation.id ? updatedConversation : conv
      )
    );
  };

  const handleEditMessage = (messageId: string, newContent: string) => {
    if (!selectedConversation) return;

    const updatedMessages = selectedConversation.messages.map(msg =>
      msg.id === messageId ? { ...msg, content: newContent } : msg
    );
    const updatedConversation = {
      ...selectedConversation,
      messages: updatedMessages,
      lastMessage: updatedMessages.length > 0 ? updatedMessages[updatedMessages.length - 1].content : 'No messages',
      lastMessageTime: updatedMessages.length > 0 ? updatedMessages[updatedMessages.length - 1].timestamp : new Date()
    };

    setSelectedConversation(updatedConversation);

    setConversations(prev =>
      prev.map(conv =>
        conv.id === selectedConversation.id ? updatedConversation : conv
      )
    );
  };

  const handleSendMessage = async (content: string) => {
    if (!selectedConversation || !isSessionReady) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };

    setConversations(prev =>
      prev.map(conv =>
        conv.id === selectedConversation.id
          ? {
              ...conv,
              messages: [...conv.messages, userMessage],
              lastMessage: content,
              lastMessageTime: new Date()
            }
          : conv
      )
    );

    setSelectedConversation(prev => prev ? {
      ...prev,
      messages: [...prev.messages, userMessage],
      lastMessage: content,
      lastMessageTime: new Date()
    } : null);

    try {
      if (selectedConversation.userId.startsWith('fb_')) {
        const response = await fetch('/api/facebook/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            recipient_id: selectedConversation.userId,
            message: content
          })
        });

        if (!response.ok) throw new Error('Failed to send Facebook message');
        setTimeout(() => loadFacebookConversations(), 2000);
      } else {
        const emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'neutral'];
        const randomEmotion = emotions[Math.floor(Math.random() * emotions.length)];

        const response = await fetch(`/api/query?session_id=${sessionId}&question=${encodeURIComponent(content)}&emotional=${randomEmotion}`, {
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

          setSelectedConversation(prev => prev ? {
            ...prev,
            messages: [...prev.messages, botMessage],
            lastMessage: result.response,
            lastMessageTime: new Date()
          } : null);
        } else {
          throw new Error('Failed to get response');
        }
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

      setSelectedConversation(prev => prev ? {
        ...prev,
        messages: [...prev.messages, errorMessage],
        lastMessage: errorMessage.content,
        lastMessageTime: new Date()
      } : null);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    loadFacebookConversations();
  };

  const filteredConversations = conversations
    .filter(conv => !conv.isArchived)
    .filter(conv =>
      conv.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conv.lastMessage.toLowerCase().includes(searchTerm.toLowerCase())
    );

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Conversations</h3>
          <p className="text-gray-500">
            {aiAssistantEnabled ? 'Connecting to Facebook Messenger...' : 'AI Assistant is disabled'}
          </p>
        </div>
      </div>
    );
  }

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
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto p-8">
          <Bot className="w-16 h-16 text-gray-300 mx-auto mb-6" />
          <h3 className="text-xl font-semibold text-gray-900 mb-4">AI Assistant Disabled</h3>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-2 mb-2">
              <AlertCircle className="w-5 h-5 text-yellow-600" />
              <span className="text-yellow-700 font-medium">Manual Mode Active</span>
            </div>
            <p className="text-yellow-700 text-sm">
              Facebook webhook processing is disabled. No old conversation history will be shown.
              Enable the AI Assistant to start receiving and responding to Facebook messages.
            </p>
          </div>
          <p className="text-gray-500 text-sm">
            Turn on the AI Assistant in the Dashboard to start managing Facebook conversations.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-gray-50">
      {error && (
        <div className="absolute top-0 left-0 right-0 bg-red-50 border-b border-red-200 p-3 z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span className="text-red-700 text-sm">{error}</span>
            </div>
            <button
              onClick={handleRefresh}
              className="text-red-600 hover:text-red-800 text-sm flex items-center space-x-1"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry</span>
            </button>
          </div>
        </div>
      )}

      <div className={`flex w-full ${error ? 'pt-12' : ''}`}>
        <ConversationList
          conversations={filteredConversations}
          selectedConversation={selectedConversation}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onConversationSelect={handleConversationSelect}
          onConversationUpdate={handleConversationUpdate}
          onConversationDelete={handleConversationDelete}
        />

        <ChatArea
          conversation={selectedConversation}
          onSendMessage={handleSendMessage}
          aiAssistantEnabled={aiAssistantEnabled}
          onDeleteMessage={handleDeleteMessage}
          onEditMessage={handleEditMessage}
        />
      </div>
    </div>
  );
};

export default ChatInterface;