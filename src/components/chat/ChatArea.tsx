import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, MoreVertical, Trash2, Edit3 } from 'lucide-react';
import { Conversation } from '../../types/chat';

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
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [hoveredMessageId, setHoveredMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages]);

  // ✅ FACEBOOK-STYLE: Auto-resize textarea with tighter constraints
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;
      const maxHeight = 100; // ✅ REDUCED: About 4 lines max (was 120px)
      const minHeight = 36;   // ✅ REDUCED: Smaller minimum height (was 44px)
      textarea.style.height = `${Math.min(Math.max(scrollHeight, minHeight), maxHeight)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputMessage]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const message = inputMessage;
    setInputMessage(''); // Clear input immediately

    try {
      await onSendMessage(message);
    } catch (error) {
      console.error('Send message error:', error);
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
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">
                  {conversation.isOnline ? 'ออนไลน์' : 'ออฟไลน์'}
                </span>
                {aiAssistantEnabled ? (
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium flex items-center space-x-1">
                    <Bot className="w-3 h-3" />
                    <span>AI Mode</span>
                  </span>
                ) : (
                  <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium flex items-center space-x-1">
                    <User className="w-3 h-3" />
                    <span>Manual Mode</span>
                  </span>
                )}
              </div>
            </div>
          </div>
          <button className="p-2 hover:bg-gray-100 rounded-lg">
            <MoreVertical className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Messages - Adjusted height to account for smaller input area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ maxHeight: 'calc(100vh - 200px)' }}>
        {conversation.messages.map((message) => {
          const isFromUser = message.type === 'user';
          const isFromAdmin = message.type === 'admin' || message.type === 'bot';
          const isEditing = editingMessageId === message.id;
          
          const canEdit = !aiAssistantEnabled && isFromAdmin;
          const canDelete = !aiAssistantEnabled && isFromAdmin;
          
          return (
            <div
              key={message.id}
              className={`flex items-start space-x-3 ${
                isFromUser ? 'justify-start' : 'justify-end'
              } group`}
              onMouseEnter={() => setHoveredMessageId(message.id)}
              onMouseLeave={() => setHoveredMessageId(null)}
            >
              {/* User Avatar - Left side for user messages */}
              {isFromUser && (
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
              
              <div className="relative">
                {isEditing ? (
                  <div className="bg-gray-100 border-2 border-blue-300 rounded-2xl p-4 max-w-md">
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
                    className={`px-4 py-3 rounded-2xl relative inline-block max-w-md ${
                      isFromUser
                        ? 'bg-gray-100 rounded-bl-md'
                        : 'bg-blue-600 text-white rounded-br-md'
                    }`}
                    style={{
                      wordWrap: 'break-word',
                      overflowWrap: 'break-word',
                      maxWidth: 'fit-content'
                    }}
                  >
                    <p className={`text-sm leading-relaxed whitespace-pre-wrap ${
                      isFromUser 
                        ? 'text-gray-900 font-medium'
                        : 'text-white'
                    }`}>
                      {message.content}
                    </p>
                    <p className={`text-xs mt-2 ${
                      isFromUser ? 'text-gray-500' : 'text-blue-200'
                    }`}>
                      {message.timestamp.toLocaleTimeString('th-TH', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                      {message.emotion && ` • ${message.emotion}`}
                    </p>

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

              {/* Admin/Bot Avatar - Right side for admin/bot messages */}
              {isFromAdmin && (
                <div className="p-2 bg-green-100 rounded-full flex-shrink-0">
                  <Bot className="w-4 h-4 text-green-600" />
                </div>
              )}
            </div>
          );
        })}
        
        <div ref={messagesEndRef} />
      </div>

      {/* ✅ FACEBOOK-STYLE: Compact Message Input Area */}
      <div className="px-4 py-2 bg-white border-t border-gray-200 flex-shrink-0">
        {/* ✅ COMPACT: Smaller status message */}
        {aiAssistantEnabled ? (
          <div className="mb-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <Bot className="w-3 h-3 text-green-600" />
              <span className="text-xs text-green-700 font-medium">
                AI Mode Active
              </span>
            </div>
          </div>
        ) : (
          <div className="mb-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <User className="w-3 h-3 text-amber-600" />
              <span className="text-xs text-amber-700 font-medium">
                Manual Mode Active
              </span>
            </div>
          </div>
        )}

        {/* ✅ FACEBOOK-STYLE: Compact input container */}
        <div className="flex items-end space-x-2 bg-gray-50 rounded-full px-3 py-2 border border-gray-200">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="พิมพ์ข้อความ..."
              className="w-full bg-transparent border-none outline-none resize-none text-sm placeholder-gray-500 leading-5"
              rows={1}
              style={{ 
                minHeight: '20px',    // ✅ FACEBOOK-STYLE: Very compact minimum
                maxHeight: '80px'     // ✅ FACEBOOK-STYLE: Smaller maximum
              }}
            />
          </div>
          
          {/* ✅ FACEBOOK-STYLE: Compact send button */}
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim()}
            className={`p-1.5 rounded-full transition-colors flex-shrink-0 ${
              !inputMessage.trim()
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-blue-600 hover:bg-blue-100'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;