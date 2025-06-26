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
          .map((conv: any) => {
            const lastMessageTime = new Date(conv.lastMessageTime);
            const timeDiff = now.getTime() - lastMessageTime.getTime();
            const isRecentMessage = timeDiff < (5 * 60 * 1000); // Last 5 minutes
            
            return {
              ...conv,
              lastMessageTime,
              messages: conv.messages.map((msg: any) => ({
                ...msg,
                timestamp: new Date(msg.timestamp),
              })),
              // ✅ CRITICAL FIX: Mark as unread if message is very recent (last 5 minutes)
              unreadCount: 0, // Keep at 0 to prevent badges
              isRead: !isRecentMessage, // Mark as unread if recent message
              // Ensure these properties exist with safe defaults
              isPinned: conv.isPinned || false,
              isMuted: conv.isMuted || false,
              isArchived: conv.isArchived || false
            };
          });

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

  // ✅ CRITICAL FIX: Always load conversations on mount, regardless of AI Assistant status
  useEffect(() => {
    loadFacebookConversations();
  }, []);

  // ✅ CRITICAL FIX: Always poll for new messages in real-time, regardless of AI Assistant status
  // This ensures that new Facebook messages appear immediately in the UI
  useEffect(() => {
    const interval = setInterval(() => {
      loadFacebookConversations();
    }, 3000); // Poll every 3 seconds for new messages

    return () => clearInterval(interval);
  }, [conversations]); // Always run, not dependent on aiAssistantEnabled

  const handleConversationSelect = (conversation: Conversation) => {
    setSelectedConversation(conversation);
    // ✅ Mark conversation as read when selected
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
          ? { 
              ...conv, 
              ...updates,
              unreadCount: updates.unreadCount !== undefined ? 0 : conv.unreadCount,
              isRead: updates.isRead !== undefined ? updates.isRead : conv.isRead
            }
          : conv
      )
    );
    if (selectedConversation?.id === conversationId) {
      setSelectedConversation(prev => prev ? { 
        ...prev, 
        ...updates,
        unreadCount: 0,
        isRead: updates.isRead !== undefined ? updates.isRead : prev.isRead
      } : null);
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
      lastMessageTime: updatedMessages.length > 0 ? updatedMessages[updatedMessages.length - 1].timestamp : new Date(),
      unreadCount: 0,
      isRead: true
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
      lastMessageTime: updatedMessages.length > 0 ? updatedMessages[updatedMessages.length - 1].timestamp : new Date(),
      unreadCount: 0,
      isRead: true
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

    // ✅ CRITICAL FIX: Admin messages should appear IMMEDIATELY on the RIGHT side
    // Create admin message that appears instantly without any loading animation
    const adminMessage: Message = {
      id: Date.now().toString(),
      type: 'admin', // Always use 'admin' type so it appears on the right side
      content,
      timestamp: new Date()
    };

    // ✅ INSTANT UPDATE: Add admin message to UI immediately - NO LOADING STATE
    const updateConversationWithAdminMessage = (conv: Conversation) => {
      if (conv.id === selectedConversation.id) {
        return {
          ...conv,
          messages: [...conv.messages, adminMessage],
          lastMessage: content,
          lastMessageTime: new Date(),
          unreadCount: 0,
          isRead: true
        };
      }
      return conv;
    };

    // Update conversations list immediately
    setConversations(prev => prev.map(updateConversationWithAdminMessage));

    // Update selected conversation immediately
    setSelectedConversation(prev => prev ? {
      ...prev,
      messages: [...prev.messages, adminMessage],
      lastMessage: content,
      lastMessageTime: new Date(),
      unreadCount: 0,
      isRead: true
    } : null);

    // ✅ BACKGROUND PROCESSING: Send message to Facebook in the background
    // This happens AFTER the message appears in the UI, so no loading animation
    try {
      if (selectedConversation.userId.startsWith('fb_')) {
        // Send to Facebook API in background - user already sees their message
        const response = await fetch('/api/facebook/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            recipient_id: selectedConversation.userId,
            message: content
          })
        });

        if (!response.ok) {
          // If sending fails, show error but keep admin message visible
          console.error('Failed to send Facebook message');
          // Optionally show a small error indicator next to the message
        }

        // Refresh conversations after sending to get any new incoming messages
        setTimeout(() => loadFacebookConversations(), 1000);
      }

      // ✅ AI PROCESSING: Only process AI response if AI Assistant is enabled
      if (aiAssistantEnabled && !selectedConversation.userId.startsWith('fb_')) {
        // For non-Facebook conversations, process AI response
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

          // Add bot response to conversation
          setConversations(prev =>
            prev.map(conv =>
              conv.id === selectedConversation.id
                ? {
                    ...conv,
                    messages: [...conv.messages, botMessage],
                    lastMessage: result.response,
                    lastMessageTime: new Date(),
                    unreadCount: 0,
                    isRead: true
                  }
                : conv
            )
          );

          setSelectedConversation(prev => prev ? {
            ...prev,
            messages: [...prev.messages, botMessage],
            lastMessage: result.response,
            lastMessageTime: new Date(),
            unreadCount: 0,
            isRead: true
          } : null);
        }
      }
    } catch (error) {
      console.error('Background processing error:', error);
      // Error handling - but admin message is already visible, so no need to show loading error
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
            {aiAssistantEnabled ? 'Connecting to Facebook Messenger...' : 'Loading conversations for manual mode...'}
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