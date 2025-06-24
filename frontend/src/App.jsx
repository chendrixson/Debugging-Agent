import React, { useState, useEffect, useRef } from 'react';
import { Bug, MessageSquare, Terminal, Activity } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import DebuggerConsole from './components/DebuggerConsole';
import StatusPanel from './components/StatusPanel';
import websocketService from './services/websocket';
import { cn } from './utils/cn';

const App = () => {
  console.log('App: Component is loading...');
  
  const [activeTab, setActiveTab] = useState('chat');
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const hasInitialized = useRef(false);

  useEffect(() => {
    console.log('App: useEffect running - hasInitialized:', hasInitialized.current);
    
    // Only initialize once, even with StrictMode double-invocation
    if (hasInitialized.current) {
      console.log('App: Already initialized, skipping WebSocket setup');
      return;
    }
    
    hasInitialized.current = true;
    
    // Connect to WebSocket
    console.log('App: Initializing WebSocket connection...');
    websocketService.connect();

    // Listen for connection status
    websocketService.on('connected', () => {
      console.log('App: Received connected event, updating status');
      setConnectionStatus('connected');
    });

    websocketService.on('disconnect', () => {
      console.log('App: Received disconnect event, updating status');
      setConnectionStatus('disconnected');
    });

    // Cleanup function - only runs on actual unmount, not StrictMode double-invocation
    return () => {
      console.log('App: useEffect cleanup running - this is normal with StrictMode');
      // Note: We don't disconnect here because the WebSocket should stay connected
      // for the lifetime of the app. The service handles reconnection gracefully.
    };
  }, []);

  const tabs = [
    {
      id: 'chat',
      label: 'Chat',
      icon: MessageSquare,
      component: ChatInterface,
    },
    {
      id: 'console',
      label: 'Console',
      icon: Terminal,
      component: DebuggerConsole,
    },
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Bug className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Debug Agent
                </h1>
                <p className="text-sm text-gray-500">
                  AI-Powered Debugging Assistant
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={cn(
                  'w-2 h-2 rounded-full',
                  connectionStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
                )} />
                <span className="text-sm text-gray-600">
                  {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              {/* Test Button */}
              <button
                onClick={() => {
                  console.log('App: Manual connection test');
                  console.log('App: Current connection status:', connectionStatus);
                  console.log('App: WebSocket service connected:', websocketService.isConnected());
                  websocketService.connect();
                }}
                className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Test Connection
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg border shadow-sm">
              {/* Tab Navigation */}
              <div className="border-b">
                <nav className="flex space-x-8 px-6">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={cn(
                          'flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                          activeTab === tab.id
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        )}
                      >
                        <Icon size={16} />
                        <span>{tab.label}</span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="h-[600px]">
                {ActiveComponent && <ActiveComponent />}
              </div>
            </div>
          </div>

          {/* Right Column - Status Panel */}
          <div className="lg:col-span-1">
            <StatusPanel />
            
            {/* Example Prompts */}
            <div className="mt-6 bg-white rounded-lg border p-4">
              <h3 className="text-lg font-semibold mb-3">Example Prompts</h3>
              <div className="space-y-2">
                <button
                  onClick={() => setActiveTab('chat')}
                  className="w-full text-left p-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                >
                  Help me debug my C++ application
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  className="w-full text-left p-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                >
                  Analyze a crash dump file
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  className="w-full text-left p-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                >
                  Help with access violation
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  className="w-full text-left p-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                >
                  Set breakpoints to debug
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App; 