import { io } from 'socket.io-client';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.eventListeners = new Map();
    this.connectionAttempts = 0;
    this.isConnecting = false;
    this.shouldStayConnected = false; // Track if we want to maintain connection
  }

  connect() {
    console.log('WebSocket: Connect requested (attempts:', this.connectionAttempts, ')');
    
    // If already connected, don't do anything
    if (this.socket && this.isConnected) {
      console.log('WebSocket: Already connected, skipping connection attempt');
      return;
    }

    // If we're in the process of connecting, don't start another connection
    if (this.isConnecting) {
      console.log('WebSocket: Connection already in progress, skipping');
      return;
    }

    // Mark that we want to stay connected
    this.shouldStayConnected = true;
    this.isConnecting = true;
    this.connectionAttempts++;

    // If there's an existing socket but not connected, clean it up first
    if (this.socket && !this.isConnected) {
      console.log('WebSocket: Cleaning up existing socket before reconnecting');
      this.socket.disconnect();
      this.socket = null;
    }

    this.socket = io('/', {
      transports: ['websocket', 'polling'],
    });

    console.log('WebSocket: Socket.io instance created, setting up event listeners...');

    this.socket.on('connect', () => {
      console.log('WebSocket: Connected to Debug Agent WebSocket');
      this.isConnected = true;
      this.isConnecting = false;
      console.log('WebSocket: Emitting connected event to listeners');
      this.emit('connected', { message: 'Connected to Debug Agent' });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket: Disconnected from Debug Agent WebSocket, reason:', reason);
      this.isConnected = false;
      this.isConnecting = false;
      
      // If we should stay connected and this wasn't an intentional disconnect, try to reconnect
      if (this.shouldStayConnected && reason !== 'io client disconnect') {
        console.log('WebSocket: Unexpected disconnect, attempting to reconnect...');
        setTimeout(() => {
          if (this.shouldStayConnected) {
            this.connect();
          }
        }, 1000);
      }
    });

    this.socket.on('debugger_event', (data) => {
      console.log('WebSocket: Received debugger_event', data);
      this.emit('debugger_event', data);
    });

    this.socket.on('tool_call_update', (data) => {
      console.log('WebSocket: Received tool_call_update', data);
      this.emit('tool_call_update', data);
    });

    this.socket.on('connected', (data) => {
      console.log('WebSocket: Received connected event', data);
      this.emit('connected', data);
    });

    // Add error handling
    this.socket.on('connect_error', (error) => {
      console.error('WebSocket: Connection error:', error);
      this.isConnecting = false;
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket: Socket error:', error);
      this.isConnecting = false;
    });

    console.log('WebSocket: Event listeners set up, connection attempt complete');
  }

  disconnect() {
    console.log('WebSocket: Disconnect requested');
    
    // Mark that we no longer want to stay connected
    this.shouldStayConnected = false;
    
    if (this.socket) {
      console.log('WebSocket: Disconnecting socket...');
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      this.isConnecting = false;
      console.log('WebSocket: Socket disconnected and cleaned up');
    } else {
      console.log('WebSocket: No socket to disconnect');
    }
  }

  on(event, callback) {
    console.log(`WebSocket: Registering listener for event '${event}'`);
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    
    const listeners = this.eventListeners.get(event);
    
    // Check if this callback is already registered
    if (listeners.includes(callback)) {
      console.log(`WebSocket: Listener for '${event}' already registered, skipping duplicate`);
      return;
    }
    
    listeners.push(callback);
    console.log(`WebSocket: Total listeners for '${event}': ${listeners.length}`);
  }

  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    console.log(`WebSocket: Emitting event '${event}' to ${this.eventListeners.has(event) ? this.eventListeners.get(event).length : 0} listeners`, data);
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        callback(data);
      });
    } else {
      console.log(`WebSocket: No listeners registered for event '${event}'`);
    }
  }

  isConnected() {
    return this.isConnected;
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService; 