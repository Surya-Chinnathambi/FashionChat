import React from 'react';
import { ChatMessage as ChatMessageType, Product } from '../types';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 chat-bubble`}>
      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
        isUser 
          ? 'bg-blue-500 text-white' 
          : 'bg-white text-gray-800 shadow-sm border'
      }`}>
        {!isUser && (
          <div className="flex items-center mb-1">
            <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mr-2">
              <i className="fas fa-robot text-white text-xs"></i>
            </div>
            <span className="text-xs text-gray-500 font-medium">Fashion Assistant</span>
            {message.intent && (
              <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                {message.intent}
              </span>
            )}
          </div>
        )}
        
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>
        
        {/* Product recommendations */}
        {message.products && message.products.length > 0 && (
          <div className="mt-3">
            <div className="text-xs text-gray-600 mb-2 font-medium">
              Product Recommendations:
            </div>
            <div className="space-y-2">
              {message.products.slice(0, 3).map((product: Product) => (
                <div key={product.id} className="bg-gray-50 p-2 rounded border product-card">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="text-xs font-semibold text-gray-800 line-clamp-1">
                        {product.name}
                      </h4>
                      <p className="text-xs text-gray-600 mt-1">
                        {product.category} • {product.color} • {product.brand}
                      </p>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-sm font-bold text-blue-600">
                          ${product.price}
                        </span>
                        {product.stock_quantity > 0 ? (
                          <span className="text-xs text-green-600">In Stock</span>
                        ) : (
                          <span className="text-xs text-red-600">Out of Stock</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Order information */}
        {message.orders && message.orders.length > 0 && (
          <div className="mt-3">
            <div className="text-xs text-gray-600 mb-2 font-medium">
              Your Orders:
            </div>
            <div className="space-y-2">
              {message.orders.slice(0, 2).map((order: any, index: number) => (
                <div key={order.id || index} className="bg-gray-50 p-2 rounded border">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-xs font-semibold">#{order.order_number}</p>
                      <p className="text-xs text-gray-600 capitalize">{order.status}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-bold">${order.total_amount}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(order.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="text-xs text-gray-400 mt-2">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
