export interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  emotion?: string;
}

export interface Conversation {
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
  isPinned?: boolean;
  isMuted?: boolean;
  isArchived?: boolean;
}