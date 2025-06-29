import React, { useState } from 'react';
import { Search, User, CheckCircle2, Circle, MoreVertical, Archive, Trash2, Pin, PinOff, Volume2, VolumeX } from 'lucide-react';
import { Conversation } from '../../types/chat';

interface ConversationListProps {
  conversations: Conversation[];
  selectedConversation: Conversation | null;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onConversationSelect: (conversation: Conversation) => void;
  onConversationUpdate: (conversationId: string, updates: Partial<Conversation>) => void;
  onConversationDelete: (conversationId: string) => void;
  onExitChat?: () => void; // ✅ NEW: Add exit chat callback
}

const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  selectedConversation,
  searchTerm,
  onSearchChange,
  onConversationSelect,
  onConversationUpdate,
  onConversationDelete  
}) => {
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

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

  const handleMenuClick = (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    setActiveMenu(activeMenu === conversationId ? null : conversationId);
  };

  const handleMenuAction = (action: string, conversation: Conversation) => {
    switch (action) {
      case 'pin':
        onConversationUpdate(conversation.id, { isPinned: !conversation.isPinned });
        break;
      case 'mute':
        onConversationUpdate(conversation.id, { isMuted: !conversation.isMuted });
        break;
      case 'archive':
        onConversationUpdate(conversation.id, { isArchived: true });
        break;
      case 'delete':
        if (window.confirm('คุณต้องการลบการสนทนานี้หรือไม่?')) {
          onConversationDelete(conversation.id);
        }
        break;
      case 'markRead':
        onConversationUpdate(conversation.id, { isRead: true, unreadCount: 0 });
        break;
      case 'markUnread':
        onConversationUpdate(conversation.id, { isRead: false, unreadCount: 0 });
        break;
    }
    setActiveMenu(null);
  };

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = () => setActiveMenu(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  // Sort conversations: pinned first, then by last message time
  const sortedConversations = [...conversations].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    return b.lastMessageTime.getTime() - a.lastMessageTime.getTime();
  });

  return (
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
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {sortedConversations.map((conversation) => {
          // ✅ CRITICAL FIX: Check if conversation has new messages AND is not currently selected
          const now = new Date();
          const timeDiff = now.getTime() - conversation.lastMessageTime.getTime();
          const isRecentMessage = timeDiff < (5 * 60 * 1000); // Last 5 minutes
          const isCurrentlySelected = selectedConversation?.id === conversation.id;
          
          // ✅ NEW LOGIC: Show dark black ONLY for new messages that are NOT currently being viewed
          const hasNewMessages = (!conversation.isRead || isRecentMessage) && !isCurrentlySelected;
          
          return (
            <div
              key={conversation.id}
              onClick={() => onConversationSelect(conversation)}
              className={`relative p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors group ${
                selectedConversation?.id === conversation.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
              } ${conversation.isMuted ? 'opacity-70' : ''}`}
            >
              {/* Pin indicator */}
              {conversation.isPinned && (
                <div className="absolute top-2 right-2">
                  <Pin className="w-3 h-3 text-blue-500 fill-current" />
                </div>
              )}

              <div className="flex items-start space-x-3">
                <div className="relative">
                  {conversation.userAvatar ? (
                    <img
                      src={conversation.userAvatar}
                      alt={conversation.userName}
                      className="w-12 h-12 rounded-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        target.nextElementSibling?.classList.remove('hidden');
                      }}
                    />
                  ) : null}
                  <div className={`w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center ${conversation.userAvatar ? 'hidden' : ''}`}>
                    <span className="text-white font-semibold text-sm">
                      {conversation.userName.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  {conversation.isOnline && (
                    <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-white rounded-full"></div>
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    {/* ✅ CRITICAL FIX: User name - DARK BLACK only for unviewed new messages, NORMAL GRAY when viewing */}
                    <h3 className={`font-medium truncate ${
                      hasNewMessages 
                        ? 'text-black font-bold' // ✅ PURE BLACK for new unviewed messages
                        : 'text-gray-600 font-medium' // ✅ NORMAL GRAY when viewing or read
                    }`}>
                      {conversation.userName}
                      {conversation.isMuted && (
                        <VolumeX className="inline w-3 h-3 ml-1 text-gray-400" />
                      )}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">
                        {formatTime(conversation.lastMessageTime)}
                      </span>
                      {/* ✅ Visual indicator for new messages */}
                      {hasNewMessages ? (
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      ) : (
                        <CheckCircle2 className="w-3 h-3 text-gray-400" />
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    {/* ✅ CRITICAL FIX: Last message - DARK BLACK only for unviewed new messages, NORMAL GRAY when viewing */}
                    <p className={`text-sm truncate flex-1 mr-2 ${
                      hasNewMessages 
                        ? 'text-black font-bold' // ✅ PURE BLACK for new unviewed messages
                        : 'text-gray-500 font-normal' // ✅ NORMAL GRAY when viewing or read
                    }`}>
                      {conversation.lastMessage}
                    </p>
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <button
                        onClick={(e) => handleMenuClick(e, conversation.id)}
                        className="p-1 hover:bg-gray-200 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <MoreVertical className="w-4 h-4 text-gray-500" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Context Menu */}
              {activeMenu === conversation.id && (
                <div className="absolute right-4 top-16 bg-white border border-gray-200 rounded-lg shadow-lg py-2 z-10 min-w-[160px]">
                  <button
                    onClick={() => handleMenuAction('pin', conversation)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2"
                  >
                    {conversation.isPinned ? (
                      <>
                        <PinOff className="w-4 h-4" />
                        <span>เลิกปักหมุด</span>
                      </>
                    ) : (
                      <>
                        <Pin className="w-4 h-4" />
                        <span>ปักหมุด</span>
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={() => handleMenuAction('mute', conversation)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2"
                  >
                    {conversation.isMuted ? (
                      <>
                        <Volume2 className="w-4 h-4" />
                        <span>เปิดเสียง</span>
                      </>
                    ) : (
                      <>
                        <VolumeX className="w-4 h-4" />
                        <span>ปิดเสียง</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => handleMenuAction(conversation.isRead ? 'markUnread' : 'markRead', conversation)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2"
                  >
                    {conversation.isRead ? (
                      <>
                        <Circle className="w-4 h-4" />
                        <span>ทำเครื่องหมายว่ายังไม่อ่าน</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        <span>ทำเครื่องหมายว่าอ่านแล้ว</span>
                      </>
                    )}
                  </button>

                  <div className="border-t border-gray-100 my-1"></div>

                  <button
                    onClick={() => handleMenuAction('archive', conversation)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2 text-orange-600"
                  >
                    <Archive className="w-4 h-4" />
                    <span>เก็บถาวร</span>
                  </button>

                  <button
                    onClick={() => handleMenuAction('delete', conversation)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center space-x-2 text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>ลบการสนทนา</span>
                  </button>
                </div>
              )}
            </div>
          );
        })}

        {/* Empty State */}
        {sortedConversations.length === 0 && (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <User className="w-12 h-12 mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">ไม่มีการสนทนา</h3>
            <p className="text-sm text-center">
              ยังไม่มีการสนทนาใดๆ<br />
              ส่งข้อความไปยังเพจ Facebook เพื่อเริ่มต้นการสนทนา
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationList;