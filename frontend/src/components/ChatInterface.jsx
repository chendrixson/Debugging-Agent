import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Trash2 } from 'lucide-react';
import { chatAPI } from '../services/api';
import websocketService from '../services/websocket';
import { cn } from '../utils/cn';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const hasSetupListeners = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    console.log('ChatInterface: useEffect running - hasSetupListeners:', hasSetupListeners.current);
    
    // Only setup listeners once, even with StrictMode double-invocation
    if (hasSetupListeners.current) {
      console.log('ChatInterface: Already setup listeners, skipping');
      return;
    }
    
    hasSetupListeners.current = true;
    
    // Load chat history on component mount
    loadChatHistory();
    
    // Set up WebSocket event listeners
    console.log('ChatInterface: Setting up WebSocket listeners...');
    
    websocketService.on('tool_call_update', (data) => {
      console.log('ChatInterface: Received tool_call_update', data);
      handleToolCallUpdate(data);
    });

    // Cleanup listeners on unmount
    return () => {
      console.log('ChatInterface: useEffect cleanup running - this is normal with StrictMode');
      // Note: We don't remove listeners here because the component might be re-rendering
      // due to StrictMode, not actually unmounting. The service will handle cleanup.
    };
  }, []);

  const loadChatHistory = async () => {
    try {
      const response = await chatAPI.getHistory();
      if (response.success) {
        setMessages(response.history || []);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const handleToolCallUpdate = (data) => {
    console.log('ChatInterface: Processing tool_call_update', data);
    
    // Extract the actual tool call info from the data structure
    const toolCallInfo = data.tool_call || data;
    const toolCallType = toolCallInfo.type;
    const toolName = toolCallInfo.tool_name;
    const toolCallId = toolCallInfo.tool_call_id;
    
    console.log('ChatInterface: Extracted tool call info:', {
      toolCallType,
      toolName,
      toolCallId,
      fullInfo: toolCallInfo
    });
    
    if (toolCallType === 'tool_call_start') {
      // Create a new tool call message for the start
      const toolCallMessage = {
        role: 'tool_call',
        content: `🔧 **Calling tool:** \`${toolName}\`\n\n**Arguments:**\n\`\`\`json\n${JSON.stringify(toolCallInfo.arguments || {}, null, 2)}\n\`\`\``,
        status: 'started',
        timestamp: new Date().toISOString(),
        toolCallId: toolCallId,
        toolName: toolName
      };

      console.log('ChatInterface: Creating new tool call message:', toolCallMessage);
      setMessages(prev => [...prev, toolCallMessage]);
      
    } else if (toolCallType === 'tool_call_complete') {
      console.log('ChatInterface: Updating tool call with completion result');
      // Update the existing tool call message with completion result
      setMessages(prev => {
        console.log('ChatInterface: Current messages before update:', prev);
        return prev.map(msg => {
          // Match by toolCallId if available, otherwise by toolName and status
          const isMatch = msg.role === 'tool_call' && 
                         msg.status === 'started' &&
                         ((toolCallId && msg.toolCallId === toolCallId) || 
                          (!toolCallId && msg.toolName === toolName));
          
          console.log('ChatInterface: Checking message match:', {
            messageRole: msg.role,
            messageStatus: msg.status,
            messageToolCallId: msg.toolCallId,
            messageToolName: msg.toolName,
            toolCallId,
            toolName,
            isMatch
          });
          
          if (isMatch) {
            const result = toolCallInfo.result;
            let content;
            
            if (result.success) {
              const resultStr = JSON.stringify(result.data || {}, null, 2);
              content = `✅ **Tool completed:** \`${toolName}\`\n\n**Result:**\n\`\`\`json\n${resultStr}\n\`\`\``;
            } else {
              content = `❌ **Tool failed:** \`${toolName}\`\n\n**Error:** ${result.error}`;
            }
            
            console.log('ChatInterface: Updating message with content:', content);
            return {
              ...msg,
              content: content,
              status: result.success ? 'completed' : 'failed',
              timestamp: new Date().toISOString()
            };
          }
          return msg;
        });
      });
      
    } else if (toolCallType === 'tool_call_error') {
      console.log('ChatInterface: Updating tool call with error');
      // Update the existing tool call message with error
      setMessages(prev => prev.map(msg => {
        // Match by toolCallId if available, otherwise by toolName and status
        const isMatch = msg.role === 'tool_call' && 
                       msg.status === 'started' &&
                       ((toolCallId && msg.toolCallId === toolCallId) || 
                        (!toolCallId && msg.toolName === toolName));
        
        if (isMatch) {
          const errorMsg = toolCallInfo.error;
          const content = `💥 **Tool error:** \`${toolName}\`\n\n**Error:** ${errorMsg}`;
          
          console.log('ChatInterface: Updating message with error content:', content);
          return {
            ...msg,
            content: content,
            status: 'error',
            timestamp: new Date().toISOString()
          };
        }
        return msg;
      }));
      
    } else {
      console.log('ChatInterface: Unknown tool call type, using fallback');
      // Fallback for unknown tool call types
      const toolCallMessage = {
        role: 'tool_call',
        content: `**Tool Call Update:** ${toolName || 'Unknown Tool'}\n\n${JSON.stringify(toolCallInfo, null, 2)}`,
        status: 'update',
        timestamp: new Date().toISOString(),
        data: toolCallInfo
      };

      setMessages(prev => [...prev, toolCallMessage]);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(inputMessage);
      if (response.success) {
        const assistantMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Add error message
        const errorMessage = {
          role: 'assistant',
          content: `Error: ${response.error}`,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = async () => {
    try {
      await chatAPI.clearHistory();
      setMessages([]);
    } catch (error) {
      console.error('Failed to clear chat:', error);
    }
  };

  const renderMessage = (message, index) => {
    const isUser = message.role === 'user';
    const isToolCall = message.role === 'tool_call';

    if (isToolCall) {
      const statusClass = `tool-call-${message.status || 'started'}`;
      return (
        <div
          key={index}
          className={cn(
            'flex mb-4 justify-start',
            'tool-call-message',
            statusClass
          )}
        >
          <div className="max-w-[80%] rounded-lg px-4 py-2">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>
      );
    }

    return (
      <div
        key={index}
        className={cn(
          'flex mb-4',
          isUser ? 'justify-end' : 'justify-start'
        )}
      >
        <div
          className={cn(
            'max-w-[80%] rounded-lg px-4 py-2',
            isUser
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-900'
          )}
        >
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <h2 className="text-lg font-semibold">AI Debugging Assistant</h2>
        <button
          onClick={clearChat}
          className="p-2 text-gray-500 hover:text-red-500 transition-colors"
          title="Clear chat"
        >
          <Trash2 size={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="text-center text-gray-500 mt-8">
            <p>Start a conversation with the AI debugging assistant</p>
            <p className="text-sm mt-2">
              Try asking: "Help me debug my C++ application"
            </p>
          </div>
        )}
        
        {messages.map(renderMessage)}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-900 rounded-lg px-4 py-2">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span>AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-white">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask the AI to help debug an application..."
            className="flex-1 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 