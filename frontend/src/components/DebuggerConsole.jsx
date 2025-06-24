import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw, Trash2 } from 'lucide-react';
import { consoleAPI } from '../services/api';
import websocketService from '../services/websocket';
import { cn } from '../utils/cn';

const DebuggerConsole = () => {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const consoleRef = useRef(null);

  useEffect(() => {
    // Load initial console events
    loadConsoleEvents();

    // Connect to WebSocket for real-time updates
    websocketService.connect();

    // Listen for debugger events
    websocketService.on('debugger_event', handleDebuggerEvent);

    return () => {
      websocketService.off('debugger_event', handleDebuggerEvent);
    };
  }, []);

  useEffect(() => {
    if (autoScroll && consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  const loadConsoleEvents = async () => {
    setIsLoading(true);
    try {
      const response = await consoleAPI.getEvents();
      if (Array.isArray(response)) {
        setEvents(response);
      } else if (response.error) {
        console.error('Failed to load console events:', response.error);
      }
    } catch (error) {
      console.error('Failed to load console events:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDebuggerEvent = (data) => {
    setEvents(prev => [...prev, data]);
  };

  const clearConsole = async () => {
    try {
      await consoleAPI.clear();
      setEvents([]);
    } catch (error) {
      console.error('Failed to clear console:', error);
    }
  };

  const getEventColor = (eventType) => {
    const colorMap = {
      'input': 'console-event-input',
      'output': 'console-event-output',
      'error': 'console-event-error',
      'system': 'console-event-system',
      'state_change': 'console-event-state',
      'breakpoint_hit': 'console-event-breakpoint',
      'exception': 'console-event-exception',
      'process_terminated': 'console-event-terminated',
    };
    return colorMap[eventType] || 'console-event-output';
  };

  const getEventTag = (eventType) => {
    const tagMap = {
      'input': '[IN]',
      'output': '[OUT]',
      'error': '[ERR]',
      'system': '[SYS]',
      'state_change': '[STATE]',
      'breakpoint_hit': '[BP]',
      'exception': '[EXC]',
      'process_terminated': '[TERM]',
    };
    return tagMap[eventType] || '[UNK]';
  };

  const renderEvent = (event, index) => {
    const eventType = event.type || 'output';
    const colorClass = getEventColor(eventType);
    const tag = getEventTag(eventType);
    const timestamp = event.timestamp || '';
    const content = event.content || '';

    return (
      <div key={index} className={cn('console-event', colorClass)}>
        {timestamp} {tag} {content}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <h2 className="text-lg font-semibold">Debugger Console</h2>
        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded"
            />
            <span>Auto-scroll</span>
          </label>
          <button
            onClick={loadConsoleEvents}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:text-blue-500 transition-colors disabled:opacity-50"
            title="Refresh console"
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={clearConsole}
            className="p-2 text-gray-500 hover:text-red-500 transition-colors"
            title="Clear console"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Console Output */}
      <div
        ref={consoleRef}
        className="flex-1 bg-console-bg text-console-text font-mono text-sm p-4 overflow-y-auto"
        style={{ fontFamily: 'Courier New, monospace' }}
      >
        {events.length === 0 && !isLoading && (
          <div className="text-gray-500">
            No debugger events captured yet. Start debugging to see output.
          </div>
        )}
        
        {events.map(renderEvent)}
        
        {isLoading && (
          <div className="text-gray-500">
            Loading console events...
          </div>
        )}
      </div>
    </div>
  );
};

export default DebuggerConsole; 