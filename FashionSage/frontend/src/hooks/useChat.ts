import { useState, useCallback, useRef, useEffect } from 'react';
import { ChatMessage, ChatResponse } from '../types';
import { ApiService } from '../services/api';

export interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  sessionId: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearChat: () => void;
  loadChatHistory: () => Promise<void>;
}

export interface ChatMessage {
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  intent?: string;
  products?: any[];
  orders?: any[];
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load chat history when session ID is available
  const loadChatHistory = useCallback(async () => {
    if (!sessionId) return;
    
    try {
      const history = await ApiService.getChatHistory(sessionId);
      
      const formattedMessages: ChatMessage[] = history.map((msg: any) => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp,
        intent: msg.intent,
      }));
      
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  }, [sessionId]);

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Add user message immediately
    const userMessage: ChatMessage = {
      type: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Send to API
      const response: ChatResponse = await ApiService.sendMessage(message.trim(), sessionId);
      
      // Update session ID if this is the first message
      if (!sessionId && response.session_id) {
        setSessionId(response.session_id);
      }

      // Add assistant response
      const assistantMessage: ChatMessage = {
        type: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        intent: response.intent,
        products: response.products,
        orders: response.orders,
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error: any) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        type: 'assistant',
        content: error.response?.data?.detail || 'I apologize, but I encountered an error processing your message. Please try again.',
        timestamp: new Date().toISOString(),
        intent: 'error',
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  // ✅ FIXED: removed `message` from dependency array
  }, [isLoading, sessionId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setIsLoading(false);
  }, []);

  return {
    messages,
    isLoading,
    sessionId,
    sendMessage,
    clearChat,
    loadChatHistory,
  };
};

export default useChat;
