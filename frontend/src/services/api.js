import axios from 'axios';

const API_BASE_URL = '/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions
export const chatAPI = {
  // Send a message to the AI
  sendMessage: async (message) => {
    const response = await api.post('/chat', { message });
    return response.data;
  },

  // Get chat history
  getHistory: async () => {
    const response = await api.get('/chat/history');
    return response.data;
  },

  // Clear chat history
  clearHistory: async () => {
    const response = await api.post('/chat/clear');
    return response.data;
  },
};

export const debuggerAPI = {
  // Get debugger status
  getStatus: async () => {
    const response = await api.get('/debugger/status');
    return response.data;
  },
};

export const consoleAPI = {
  // Get console events
  getEvents: async () => {
    const response = await api.get('/console/events');
    return response.data;
  },

  // Clear console
  clear: async () => {
    const response = await api.post('/console/clear');
    return response.data;
  },
};

export default api; 