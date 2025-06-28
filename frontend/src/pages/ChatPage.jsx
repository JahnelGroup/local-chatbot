import React, { useState } from 'react';
import ChatBox from '../components/ChatBox';
import InputBar from '../components/InputBar';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (query) => {
    // Add user message
    const userMessage = {
      type: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, { query });
      
      const botMessage = {
        type: 'bot',
        content: response.data.response,
        sources: response.data.sources || [],
        citations: response.data.citations || [],
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        type: 'bot',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <ChatBox messages={messages} />
      <InputBar onSubmit={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};

export default ChatPage; 