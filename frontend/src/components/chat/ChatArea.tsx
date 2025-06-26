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
  const [isLoading, setIsLoading] = useState(false);
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

  // ✅ FACEBOOK-STYLE: Perfect auto-resize functionality
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;
      const minHeight = 18;   // ✅ ULTRA COMPACT: Even smaller minimum
      const maxHeight = 80;   // ✅ COMPACT: Smaller maximum for clean look
      const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
      textarea.style.height = `${newHeight}px`;
      textarea.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputMessage]);

  useEffect(() => {
    adjustTextareaHeight();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    setTimeout(() => adjustTextareaHeight(), 0);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const message = inputMessage;
    setInputMessage('');
    setTimeout(() => adjustTextareaHeight(), 0);
    setIsLoading(true);

    try {
      await onSendMessage(message);
    } catch (error) {
      console.error('Send message error:', error);
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
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center">
          <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">เลือกการสนทนา</h3>
          <p className="text-gray-500">เลือกการสนทนาจากรายการด้านซ้ายเพื่อเริ่มต้น</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* ✅ CLEAN: Minimal header with essential info only */}
      <div className="px-4 py-3 bg-white border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-gray-600" />
              </div>
              {conversation.isOnline && (
                <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 border border-white rounded-full"></div>
              )}
            </div>
            <div>
              <h3 className="font-medium text-gray-900 text-sm">{conversation.userName}</h3>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">
                  {conversation.isOnline ? 'ออนไลน์' : 'ออฟไลน์'}
                </span>
                {/* ✅ MINIMAL: Smaller status badges */}
                {aiAssistantEnabled ? (
                  <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-xs font-medium flex items-center space-x-1">
                    <Bot className="w-2.5 h-2.5" />
                    <span>AI</span>
                  </span>
                ) : (
                  <span className="px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded text-xs font-medium flex items-center space-x-1">
                    <User className="w-2.5 h-2.5" />
                    <span>Manual</span>
                  </span>
                )}
              </div>
            </div>
          </div>
          <button className="p-1.5 hover:bg-gray-100 rounded-lg">
            <MoreVertical className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* ✅ CLEAN: Messages area with minimal padding */}
      <div className="flex-1 overflow-y-auto px-4 py-2" style={{ maxHeight: 'calc(100vh - 160px)' }}>
        <div className="space-y-2">
          {conversation.messages.map((message) => {
            const isFromUser = message.type === 'user';
            const isFromAdmin = message.type === 'admin' || message.type === 'bot';
            const isEditing = editingMessageId === message.id;
            
            const canEdit = !aiAssistantEnabled && isFromAdmin;
            const canDelete = !aiAssistantEnabled && isFromAdmin;
            
            return (
              <div
                key={message.id}
                className={`flex items-start space-x-2 ${
                  isFromUser ? 'justify-start' : 'justify-end'
                } group`}
                onMouseEnter={() => setHoveredMessageId(message.id)}
                onMouseLeave={() => setHoveredMessageId(null)}
              >
                {/* ✅ CLEAN: Smaller avatars for user messages */}
                {isFromUser && (
                  <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <User className="w-3 h-3 text-white" />
                  </div>
                )}
                
                <div className="relative max-w-xs lg:max-w-md">
                  {isEditing ? (
                    <div className="bg-gray-100 border border-blue-300 rounded-2xl p-3">
                      <textarea
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        onKeyPress={handleEditKeyPress}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none text-sm"
                        rows={2}
                        autoFocus
                      />
                      <div className="flex justify-end space-x-2 mt-2">
                        <button
                          onClick={handleCancelEdit}
                          className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
                        >
                          ยกเลิก
                        </button>
                        <button
                          onClick={handleSaveEdit}
                          className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          บันทึก
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div
                      className={`px-3 py-2 rounded-2xl relative inline-block ${
                        isFromUser
                          ? 'bg-gray-100 rounded-bl-md text-gray-900'
                          : 'bg-blue-600 text-white rounded-br-md'
                      }`}
                      style={{
                        wordWrap: 'break-word',
                        overflowWrap: 'break-word',
                        maxWidth: 'fit-content'
                      }}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                      {/* ✅ CLEAN: Minimal timestamp */}
                      <p className={`text-xs mt-1 ${
                        isFromUser ? 'text-gray-500' : 'text-blue-200'
                      }`}>
                        {message.timestamp.toLocaleTimeString('th-TH', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </p>

                      {/* ✅ CLEAN: Minimal edit/delete buttons */}
                      {(canEdit || canDelete) && hoveredMessageId === message.id && (
                        <div className="absolute -top-1 -right-1 flex space-x-0.5 bg-white rounded-lg shadow-md border border-gray-200 p-0.5 z-10">
                          {canEdit && (
                            <button
                              onClick={() => handleEditMessage(message.id, message.content)}
                              className="p-1 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                              title="แก้ไขข้อความ"
                            >
                              <Edit3 className="w-2.5 h-2.5" />
                            </button>
                          )}
                          {canDelete && (
                            <button
                              onClick={() => handleDeleteMessage(message.id)}
                              className="p-1 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                              title="ลบข้อความ"
                            >
                              <Trash2 className="w-2.5 h-2.5" />
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* ✅ CLEAN: Smaller avatars for admin/bot messages */}
                {isFromAdmin && (
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot className="w-3 h-3 text-green-600" />
                  </div>
                )}
              </div>
            );
          })}
          
          {/* ✅ CLEAN: Minimal loading indicator */}
          {isLoading && (
            <div className="flex items-start space-x-2 justify-end">
              <div className="bg-blue-100 rounded-2xl rounded-br-md px-3 py-2">
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
              <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-3 h-3 text-green-600" />
              </div>
            </div>
          )}
        </div>
        
        <div ref={messagesEndRef} />
      </div>

      {/* ✅ FACEBOOK-STYLE: Ultra clean input area */}
      <div className="px-4 py-2 bg-white border-t border-gray-100">
        {/* ✅ MINIMAL: Only show status when in manual mode */}
        {!aiAssistantEnabled && (
          <div className="mb-2 px-2 py-1 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-center space-x-1">
              <User className="w-3 h-3 text-amber-600" />
              <span className="text-xs text-amber-700 font-medium">
                Manual Mode
              </span>
            </div>
          </div>
        )}

        {/* ✅ FACEBOOK-STYLE: Clean input container exactly like your image */}
        <div className="flex items-end space-x-2 bg-gray-50 rounded-full px-3 py-1.5 border border-gray-200 hover:border-gray-300 focus-within:border-blue-500 transition-colors">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="พิมพ์ข้อความ..."
              disabled={isLoading}
              className="w-full bg-transparent border-none outline-none resize-none text-sm placeholder-gray-500 leading-4"
              rows={1}
              style={{ 
                minHeight: '18px',
                maxHeight: '80px',
                overflowY: 'hidden',
                paddingTop: '1px',
                paddingBottom: '1px',
                lineHeight: '18px'
              }}
            />
          </div>
          
          {/* ✅ FACEBOOK-STYLE: Minimal send button */}
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className={`p-1 rounded-full transition-all duration-200 flex-shrink-0 ${
              !inputMessage.trim() || isLoading
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-blue-600 hover:bg-blue-100'
            }`}
          >
            {isLoading ? (
              <div className="w-3.5 h-3.5 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;