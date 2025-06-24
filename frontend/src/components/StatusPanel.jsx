import React, { useState, useEffect } from 'react';
import { RefreshCw, Circle, Square, Play, Pause } from 'lucide-react';
import { debuggerAPI } from '../services/api';
import { cn } from '../utils/cn';

const StatusPanel = () => {
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    loadStatus();
    
    // Refresh status every 5 seconds
    const interval = setInterval(loadStatus, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    setIsLoading(true);
    try {
      const response = await debuggerAPI.getStatus();
      setStatus(response);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load debugger status:', error);
      setStatus({ error: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (state) => {
    const stateLower = state?.toLowerCase() || '';
    
    if (stateLower.includes('running') || stateLower.includes('attached')) {
      return <Play size={16} className="text-green-500" />;
    } else if (stateLower.includes('stopped') || stateLower.includes('paused')) {
      return <Pause size={16} className="text-yellow-500" />;
    } else if (stateLower.includes('terminated') || stateLower.includes('detached')) {
      return <Square size={16} className="text-red-500" />;
    } else {
      return <Circle size={16} className="text-gray-500" />;
    }
  };

  const getStatusColor = (state) => {
    const stateLower = state?.toLowerCase() || '';
    
    if (stateLower.includes('running') || stateLower.includes('attached')) {
      return 'text-green-600';
    } else if (stateLower.includes('stopped') || stateLower.includes('paused')) {
      return 'text-yellow-600';
    } else if (stateLower.includes('terminated') || stateLower.includes('detached')) {
      return 'text-red-600';
    } else {
      return 'text-gray-600';
    }
  };

  if (status?.error) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Debugger Status</h2>
          <button
            onClick={loadStatus}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:text-blue-500 transition-colors disabled:opacity-50"
            title="Refresh status"
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
        
        <div className="text-red-600 bg-red-50 p-3 rounded-md">
          <p className="font-medium">Error loading status:</p>
          <p className="text-sm">{status.error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Debugger Status</h2>
        <button
          onClick={loadStatus}
          disabled={isLoading}
          className="p-2 text-gray-500 hover:text-blue-500 transition-colors disabled:opacity-50"
          title="Refresh status"
        >
          <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
        </button>
      </div>

      {status ? (
        <div className="space-y-3">
          {/* Debugger State */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">State:</span>
            <div className="flex items-center space-x-2">
              {getStatusIcon(status.state)}
              <span className={cn('text-sm font-medium', getStatusColor(status.state))}>
                {status.state || 'Unknown'}
              </span>
            </div>
          </div>

          {/* Attached Status */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Attached:</span>
            <div className="flex items-center space-x-2">
              <div className={cn(
                'w-2 h-2 rounded-full',
                status.attached ? 'bg-green-500' : 'bg-gray-400'
              )} />
              <span className="text-sm">
                {status.attached ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {/* Target PID */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Target PID:</span>
            <span className="text-sm font-mono">
              {status.target_pid || 'None'}
            </span>
          </div>

          {/* Breakpoints */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Breakpoints:</span>
            <span className="text-sm font-mono">
              {status.breakpoints || 0}
            </span>
          </div>

          {/* Last Updated */}
          {lastUpdated && (
            <div className="pt-2 border-t">
              <span className="text-xs text-gray-500">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center text-gray-500 py-4">
          {isLoading ? 'Loading status...' : 'No status available'}
        </div>
      )}
    </div>
  );
};

export default StatusPanel; 