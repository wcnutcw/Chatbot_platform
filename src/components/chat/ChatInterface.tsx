import React, { useState,  useEffect } from 'react';
import {  Bot,  AlertCircle } from 'lucide-react';
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

  // Load Facebook conversations from backend
  const loadFacebookConversations = async () => {
    try {
      const response = await fetch('/api/facebook/conversations');
      if (response.ok) {
        const data = await response.json();
        const fbConversations = data.conversations || [];
        
        // Convert timestamp strings to Date objects
        const processedConversations = fbConversations.map((conv: any) => ({
          ...conv,
          lastMessageTime: new Date(conv.lastMessageTime),
          messages: conv.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }));
        
        setConversations(processedConversations);
        if (processedConversations.length > 0 && !selectedConversation) {
          setSelectedConversation(processedConversations[0]);
        }
      } else {
        // Fallback to demo data if no Facebook conversations
        const demoConversations = getDemoConversations();
        setConversations(demoConversations);
        setSelectedConversation(demoConversations[0]);
      }
    } catch (error) {
      console.error('Error loading Facebook conversations:', error);
      // Fallback to demo data
      const demoConversations = getDemoConversations();
      setConversations(demoConversations);
      setSelectedConversation(demoConversations[0]);
    } finally {
      setLoading(false);
    }
  };

  // Demo conversations fallback
  const getDemoConversations = (): Conversation[] => [
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
      isPinned: true,
      isMuted: false,
      isArchived: false,
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
      isPinned: false,
      isMuted: false,
      isArchived: false,
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
      isPinned: false,
      isMuted: false,
      isArchived: false,
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
      isPinned: false,
      isMuted: false,
      isArchived: false,
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
      isPinned: false,
      isMuted: false,
      isArchived: false,
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
      isPinned: false,
      isMuted: false,
      isArchived: false,
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
  ];

  // Load conversations on component mount
  useEffect(() => {
    loadFacebookConversations();
  }, []);

  // Poll for new messages every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (aiAssistantEnabled) {
        loadFacebookConversations();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [aiAssistantEnabled]);

  const handleConversationSelect = (conversation: Conversation) => {
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

  const handleConversationUpdate = (conversationId: string, updates: Partial<Conversation>) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversationId 
          ? { ...conv, ...updates }
          : conv
      )
    );
  };

  const handleConversationDelete = (conversationId: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== conversationId));
    if (selectedConversation?.id === conversationId) {
      setSelectedConversation(conversations.find(conv => conv.id !== conversationId) || null);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!selectedConversation || !isSessionReady || !aiAssistantEnabled) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };

    // Add user message to conversation
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

    try {
      // Check if this is a Facebook conversation
      if (selectedConversation.userId.startsWith('fb_')) {
        // Send message via Facebook API
        const response = await fetch('/api/facebook/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            recipient_id: selectedConversation.userId.replace('fb_', ''),
            message: content
          })
        });

        if (!response.ok) {
          throw new Error('Failed to send Facebook message');
        }
      } else {
        // Regular query for non-Facebook conversations
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
    }
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
          <p className="text-gray-500">Connecting to Facebook Messenger...</p>
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
      />
    </div>
  );
};

export default ChatInterface;