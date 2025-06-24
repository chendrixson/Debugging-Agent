"""Flask backend for the Debug Agent."""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import json
from datetime import datetime
from collections import deque

# Import the existing debug agent components
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from src.debugger.factory import DebuggerFactory
    from src.debugger.base import DebuggerEventType, DebuggerEvent
    from src.ai.tool_registry import ToolRegistry
    from src.ai.completion_handler import CompletionHandler
    from src.utils.config import config
    from src.utils.exceptions import DebugAgentError
except ImportError:
    from debugger.factory import DebuggerFactory
    from debugger.base import DebuggerEventType, DebuggerEvent
    from ai.tool_registry import ToolRegistry
    from ai.completion_handler import CompletionHandler
    from utils.config import config
    from utils.exceptions import DebugAgentError

class DebugAgentBackend:
    """Backend service for the Debug Agent."""
    
    def __init__(self):
        # Initialize debugger using factory
        self.debugger = DebuggerFactory.create_debugger()
        
        # Initialize AI components
        self.tool_registry = ToolRegistry(self.debugger)
        self.completion_handler = CompletionHandler(self.debugger, self.tool_registry)
        
        # Set up tool call callback
        self.completion_handler.set_tool_call_callback(self._handle_tool_call)
        
        # Chat history for UI
        self.chat_history = []
        
        # Console event storage - use deque for efficient append/pop operations
        self.console_events = deque(maxlen=1000)  # Keep last 1000 events
        self._last_event_count = 0
        
        # WebSocket clients
        self.connected_clients = set()
        
        # Register event callbacks to capture debugger events
        self._register_debugger_events()
    
    def _register_debugger_events(self):
        """Register callbacks for all debugger event types."""
        for event_type in DebuggerEventType:
            self.debugger.register_event_callback(event_type, self._handle_debugger_event)
    
    def _handle_debugger_event(self, event: DebuggerEvent):
        """Handle debugger events and store them for console display."""
        # Store the event for console display
        self.console_events.append(event)
        
        # Broadcast to connected WebSocket clients
        self._broadcast_event(event)
    
    def _handle_tool_call(self, tool_call_info: dict):
        """Handle tool call notifications from the completion handler."""
        tool_call_type = tool_call_info["type"]
        tool_name = tool_call_info["tool_name"]
        
        if tool_call_type == "tool_call_start":
            # Add tool call start message to chat history
            args_str = json.dumps(tool_call_info["arguments"], indent=2)
            tool_message = f"🔧 **Executing tool:** `{tool_name}`\n\n**Arguments:**\n```json\n{args_str}\n```"
            self.chat_history.append({
                "role": "tool_call",
                "content": tool_message,
                "tool_name": tool_name,
                "status": "started",
                "timestamp": datetime.now().isoformat()
            })
            
        elif tool_call_type == "tool_call_complete":
            # Update the tool call message with results
            result = tool_call_info["result"]
            if result.success:
                result_str = json.dumps(result.data, indent=2)
                tool_message = f"✅ **Tool completed:** `{tool_name}`\n\n**Result:**\n```json\n{result_str}\n```"
            else:
                tool_message = f"❌ **Tool failed:** `{tool_name}`\n\n**Error:** {result.error}"
            
            # Convert ToolResult to dict for socketio serialization
            tool_call_info["result"] = result.dict() if hasattr(result, "dict") else result
            
        elif tool_call_type == "tool_call_error":
            # Update the tool call message with error
            error_msg = tool_call_info["error"]
            tool_message = f"💥 **Tool error:** `{tool_name}`\n\n**Error:** {error_msg}"
            
        # Broadcast tool call update to connected clients
        self._broadcast_tool_call(tool_call_info)
    
    def _broadcast_event(self, event: DebuggerEvent):
        """Broadcast debugger event to connected WebSocket clients."""
        event_data = {
            "type": "debugger_event",
            "event_type": event.type.value,
            "timestamp": event.timestamp,
            "content": event.content
        }
        
        # Use Flask-SocketIO to emit to all connected clients
        if hasattr(self, 'socketio'):
            self.socketio.emit('debugger_event', event_data)
    
    def _broadcast_tool_call(self, tool_call_info: dict):
        """Broadcast tool call update to connected WebSocket clients."""
        tool_call_data = {
            "type": "tool_call_update",
            "tool_call": tool_call_info
        }
        
        # Use Flask-SocketIO to emit to all connected clients
        if hasattr(self, 'socketio'):
            self.socketio.emit('tool_call_update', tool_call_data)
    
    def get_debugger_status(self):
        """Get current debugger status."""
        try:
            state = self.debugger.get_state()
            status_info = {
                "state": state.value.title(),
                "target_pid": self.debugger.target_pid or None,
                "attached": self.debugger.is_attached(),
                "breakpoints": len(self.debugger.list_breakpoints()) if self.debugger.list_breakpoints() else 0
            }
            return status_info
        except Exception as e:
            return {"error": str(e)}
    
    def get_console_events(self):
        """Get the current debugger console events."""
        try:
            events = []
            for event in self.console_events:
                events.append({
                    "type": event.type.value,
                    "timestamp": event.timestamp,
                    "content": event.content
                })
            return events
        except Exception as e:
            return {"error": str(e)}
    
    def clear_console(self):
        """Clear the debugger console log."""
        try:
            self.console_events.clear()
            return {"success": True, "message": "Console cleared"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_chat_history(self):
        """Clear the chat history."""
        try:
            self.completion_handler.clear_history()
            self.chat_history.clear()
            return {"success": True, "message": "Chat history cleared"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Create Flask app
app = Flask(__name__)
CORS(app)

# Create SocketIO instance
socketio = SocketIO(app, cors_allowed_origins="*")

# Create backend instance
backend = DebugAgentBackend()
backend.socketio = socketio

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    backend.connected_clients.add(request.sid)
    emit('connected', {'message': 'Connected to Debug Agent'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")
    backend.connected_clients.discard(request.sid)


# REST API endpoints
@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat interaction with the AI debugger."""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Add user message to chat history
        backend.chat_history.append({
            "role": "user", 
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        # Get AI response, this will add tool calls to the chat_history
        ai_response = backend.completion_handler.process_message(message)
        
        # Update history with OpenAI-style messages
        backend.chat_history.append({
            "role": "assistant", 
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            "response": ai_response,
            "success": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history."""
    try:
        return jsonify({
            "history": backend.chat_history,
            "success": True
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear chat history."""
    try:
        result = backend.clear_chat_history()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/debugger/status', methods=['GET'])
def get_debugger_status():
    """Get debugger status."""
    try:
        status = backend.get_debugger_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/console/events', methods=['GET'])
def get_console_events():
    """Get console events."""
    try:
        events = backend.get_console_events()
        return jsonify(events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/console/clear', methods=['POST'])
def clear_console():
    """Clear console."""
    try:
        result = backend.clear_console()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


if __name__ == '__main__':
    print("🐛 Starting Debug Agent Backend...")
    print(f"Platform: {sys.platform}")
    print(f"OpenAI Model: {config.openai_model}")
    
    # Run the Flask app with SocketIO
    socketio.run(
        app, 
        host='127.0.0.1', 
        port=5000, 
        debug=True,
        allow_unsafe_werkzeug=True
    ) 