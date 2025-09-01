import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import { useChat } from '../hooks/useChat';

interface ChatWidgetProps {
  isAuthenticated: boolean;
  onLoginClick: () => void;
}

const ChatWidget: React.FC<ChatWidgetProps> = ({ isAuthenticated, onLoginClick }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const { messages, isLoading, sendMessage, clearChat } = useChat();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const message = inputMessage;
    setInputMessage('');
    await sendMessage(message);
  };

  const handleQuickMessage = (message: string) => {
    sendMessage(message);
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 animate-bounce-gentle"
        >
          <i className="fas fa-comments text-xl"></i>
        </button>
      </div>
    );
  }

  return (
    <div className={`fixed bottom-4 right-4 z-50 transition-all duration-300 ${
      isMinimized ? 'w-80' : 'w-96'
    }`}>
      <div className="bg-white rounded-2xl shadow-2xl chat-widget overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                <i className="fas fa-robot"></i>
              </div>
              <div>
                <h3 className="font-semibold">Fashion Assistant</h3>
                <p className="text-xs opacity-90">
                  {isLoading ? 'Typing...' : 'Online'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="text-white hover:bg-white hover:bg-opacity-20 p-1 rounded"
              >
                <i className={`fas ${isMinimized ? 'fa-expand' : 'fa-minus'}`}></i>
              </button>
              <button
                onClick={clearChat}
                className="text-white hover:bg-white hover:bg-opacity-20 p-1 rounded"
                title="Clear chat"
              >
                <i className="fas fa-trash-alt"></i>
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="text-white hover:bg-white hover:bg-opacity-20 p-1 rounded"
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Messages */}
            <div className="h-96 overflow-y-auto p-4 bg-gray-50">
              {messages.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-6xl text-gray-300 mb-4">
                    <i className="fas fa-comments"></i>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">
                    Welcome to Fashion Assistant!
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">
                    I can help you find products, track orders, and answer fashion questions.
                  </p>
                  
                  {/* Quick action buttons */}
                  <div className="space-y-2">
                    <button
                      onClick={() => handleQuickMessage("Show me some dresses")}
                      className="block w-full text-left p-2 bg-white rounded-lg hover:bg-gray-100 transition-colors text-sm border"
                    >
                      <i className="fas fa-search mr-2 text-blue-500"></i>
                      Show me some dresses
                    </button>
                    <button
                      onClick={() => handleQuickMessage("I'm looking for shoes")}
                      className="block w-full text-left p-2 bg-white rounded-lg hover:bg-gray-100 transition-colors text-sm border"
                    >
                      <i className="fas fa-shoe-prints mr-2 text-green-500"></i>
                      I'm looking for shoes
                    </button>
                    {isAuthenticated && (
                      <button
                        onClick={() => handleQuickMessage("Check my order status")}
                        className="block w-full text-left p-2 bg-white rounded-lg hover:bg-gray-100 transition-colors text-sm border"
                      >
                        <i className="fas fa-box mr-2 text-purple-500"></i>
                        Check my order status
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((message, index) => (
                    <ChatMessage key={index} message={message} />
                  ))}
                  {isLoading && (
                    <div className="flex justify-start mb-4">
                      <div className="bg-white text-gray-800 px-4 py-2 rounded-lg shadow-sm border">
                        <div className="flex items-center space-x-1 typing-indicator">
                          <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Auth prompt for order-related features */}
            {!isAuthenticated && (
              <div className="px-4 py-2 bg-blue-50 border-t">
                <p className="text-xs text-blue-600 text-center">
                  <button 
                    onClick={onLoginClick}
                    className="font-semibold hover:underline"
                  >
                    Sign in
                  </button> to track orders and get personalized recommendations
                </p>
              </div>
            )}

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t bg-white">
              <div className="flex space-x-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask about fashion, products, or orders..."
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !inputMessage.trim()}
                  className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
                >
                  <i className="fas fa-paper-plane"></i>
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default ChatWidget;
