import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, MoreVertical, Trash2, Edit3 } from 'lucide-react';
import { Conversation, Message } from '../../types/chat';

interface ChatAreaProps {
  conversation: Conversation | null;
  onSendMessage: (message: string) => Promise<void>;
  aiAssistantEnabled?: boolean;
  onDeleteMessage?: (messageId: string) => void;
  onEditMessage?: (messageId: string, newContent: string) => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({ 
  conversation, 
  onSendMessage, 
  aiAssistantEnabled = true,
  onDeleteMessage,
  onEditMessage 
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [hoveredMessageId, setHoveredMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const message = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      await onSendMessage(message);
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

  const handleDeleteMessage = (messageId: string) => {
    if (window.confirm('คุณต้องการลบข้อความนี้หรือไม่?')) {
      onDeleteMessage?.(messageId);
    }
  };

  const handleEditMessage = (messageId: string, currentContent: string) => {
    setEditingMessageId(messageId);
    setEditingContent(currentContent);
  };

  const handleSaveEdit = () => {
    if (editingMessageId && editingContent.trim()) {
      onEditMessage?.(editingMessageId, editingContent.trim());
      setEditingMessageId(null);
      setEditingContent('');
    }
  };

  const handleCancelEdit = () => {
    setEditingMessageId(null);
    setEditingContent('');
  };

  const handleEditKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">เลือกการสนทนา</h3>
          <p className="text-gray-500">เลือกการสนทนาจากรายการด้านซ้ายเพื่อเริ่มต้น</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Chat Header */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-gray-600" />
              </div>
              {conversation.isOnline && (
                <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
              )}
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{conversation.userName}</h3>
              <p className="text-sm text-gray-500">
                {conversation.isOnline ? 'ออนไลน์' : 'ออฟไลน์'}
                {!aiAssistantEnabled && (
                  <span className="ml-2 px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs">
                    Manual Mode
                  </span>
                )}
              </p>
            </div>
          </div>
          <button className="p-2 hover:bg-gray-100 rounded-lg">
            <MoreVertical className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Messages - Fixed height calculation to ensure all messages are visible */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ maxHeight: 'calc(100vh - 240px)' }}>
        {conversation.messages.map((message) => {
          const isUser = message.type === 'user';
          const isEditing = editingMessageId === message.id;
          const canEdit = !aiAssistantEnabled && isUser;
          const canDelete = !aiAssistantEnabled && isUser;
          
          return (
            <div
              key={message.id}
              className={`flex items-start space-x-3 ${
                isUser ? 'justify-start' : 'justify-end'
              } group`}
              onMouseEnter={() => setHoveredMessageId(message.id)}
              onMouseLeave={() => setHoveredMessageId(null)}
            >
              {/* User Avatar - Left side for user messages */}
              {isUser && (
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
              
              <div className="relative flex-1 max-w-[70%]">
                {isEditing ? (
                  <div className="bg-gray-100 border-2 border-blue-300 rounded-2xl p-4">
                    <textarea
                      value={editingContent}
                      onChange={(e) => setEditingContent(e.target.value)}
                      onKeyPress={handleEditKeyPress}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      rows={3}
                      autoFocus
                    />
                    <div className="flex justify-end space-x-2 mt-2">
                      <button
                        onClick={handleCancelEdit}
                        className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                      >
                        ยกเลิก
                      </button>
                      <button
                        onClick={handleSaveEdit}
                        className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                      >
                        บันทึก
                      </button>
                    </div>
                  </div>
                ) : (
                  <div
                    className={`px-4 py-3 rounded-2xl relative break-words ${
                      isUser
                        ? 'bg-gray-100 text-gray-900 rounded-bl-md'
                        : 'bg-blue-600 text-white rounded-br-md'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                    <p className={`text-xs mt-2 ${
                      isUser ? 'text-gray-500' : 'text-blue-200'
                    }`}>
                      {message.timestamp.toLocaleTimeString('th-TH', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                      {message.emotion && ` • ${message.emotion}`}
                    </p>

                    {/* Message Actions */}
                    {(canEdit || canDelete) && hoveredMessageId === message.id && (
                      <div className="absolute -top-2 -right-2 flex space-x-1 bg-white rounded-lg shadow-lg border border-gray-200 p-1 z-10">
                        {canEdit && (
                          <button
                            onClick={() => handleEditMessage(message.id, message.content)}
                            className="p-1 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                            title="แก้ไขข้อความ"
                          >
                            <Edit3 className="w-3 h-3" />
                          </button>
                        )}
                        {canDelete && (
                          <button
                            onClick={() => handleDeleteMessage(message.id)}
                            className="p-1 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                            title="ลบข้อความ"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Bot Avatar - Right side for bot messages */}
              {!isUser && (
                <div className="p-2 bg-green-100 rounded-full flex-shrink-0">
                  <Bot className="w-4 h-4 text-green-600" />
                </div>
              )}
            </div>
          );
        })}
        
        {isLoading && (
          <div className="flex items-start space-x-3 justify-end">
            <div className="bg-blue-100 rounded-2xl rounded-br-md px-4 py-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
            <div className="p-2 bg-green-100 rounded-full flex-shrink-0">
              <Bot className="w-4 h-4 text-green-600" />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input - Optimized size */}
      <div className="p-4 bg-white border-t border-gray-200 flex-shrink-0">
        {!aiAssistantEnabled && (
          <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <User className="w-4 h-4 text-amber-600" />
              <span className="text-sm text-amber-700 font-medium">
                Manual Mode Active: You can edit and delete your messages. Hover over your messages to see options.
              </span>
            </div>
          </div>
        )}

        <div className="flex space-x-3 items-end">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="พิมพ์ข้อความ..."
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2.5 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-1.5 text-sm font-medium"
          >
            <Send className="w-3.5 h-3.5" />
            <span>ส่ง</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;