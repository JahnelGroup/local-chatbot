import React, { useEffect, useRef } from 'react';

const ChatBox = ({ messages }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const renderCitation = (citation, index) => {
    // Handle page display more robustly
    const pageDisplay = citation.page && citation.page !== 'N/A' ? `Page ${citation.page}` : 'Page not specified';
    const relevancePercentage = Math.round((citation.relevance_score || 0) * 100);
    
    return (
      <div key={index} className="mb-3 p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">
        <div className="flex items-center justify-between mb-2">
          <div className="font-medium text-sm text-gray-700">
            📄 {citation.source || 'Unknown source'} • {pageDisplay}
          </div>
          <div className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded">
            [{index + 1}] Relevance: {relevancePercentage}%
          </div>
        </div>
        <blockquote className="text-sm text-gray-600 italic border-l-2 border-gray-300 pl-3 ml-2">
          "{citation.excerpt && citation.excerpt.length > 300 ? citation.excerpt.substring(0, 300) + '...' : citation.excerpt || 'No excerpt available'}"
        </blockquote>
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-chat-bg">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 mt-12">
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-lg font-medium">Welcome to Local Chatbot</h3>
          <p className="text-sm">Upload some PDF documents and start asking questions!</p>
        </div>
      ) : (
        messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-4xl px-4 py-3 rounded-lg shadow-sm ${
                message.type === 'user'
                  ? 'bg-chat-user text-white max-w-xs lg:max-w-md'
                  : 'bg-white text-gray-800 border border-gray-200'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
              
              {/* Enhanced Citations Section */}
              {message.citations && message.citations.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center mb-3">
                    <span className="text-sm font-semibold text-gray-700">📚 Sources & Citations</span>
                    <span className="ml-2 text-xs text-gray-500 bg-blue-100 px-2 py-1 rounded-full">
                      {message.citations.length} reference{message.citations.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="space-y-3">
                    {message.citations.map((citation, idx) => renderCitation(citation, idx))}
                  </div>
                </div>
              )}

              {/* Fallback for legacy sources */}
              {message.sources && message.sources.length > 0 && !message.citations && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <p className="text-xs text-gray-500 font-medium">Sources:</p>
                  <ul className="text-xs text-gray-600">
                    {message.sources.map((source, idx) => (
                      <li key={idx} className="truncate">• {source}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className="text-xs text-gray-400 mt-2">
                {message.timestamp}
              </div>
            </div>
          </div>
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatBox; 