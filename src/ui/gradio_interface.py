"""Gradio web interface for the debug agent."""

import gradio as gr
import sys
import time
import threading
import json
from typing import List, Tuple, Optional
from collections import deque
from datetime import datetime

# Handle imports for both package and direct execution
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


class DebugAgentInterface:
    """Gradio interface for the debug agent."""
    
    def __init__(self):
        # Initialize debugger using factory
        self.debugger = DebuggerFactory.create_debugger()
        
        # Initialize AI components
        self.tool_registry = ToolRegistry(self.debugger)
        self.completion_handler = CompletionHandler(self.debugger, self.tool_registry)
        
        # Set up tool call callback
        self.completion_handler.set_tool_call_callback(self._handle_tool_call)
        
        # Chat history for UI
        self.chat_history: List[dict] = []
        
        # Console event storage - use deque for efficient append/pop operations
        self.console_events: deque = deque(maxlen=1000)  # Keep last 1000 events
        self._last_event_count = 0  # Track for efficient auto-refresh
        
        # Auto-refresh control
        self._auto_refresh_enabled = False
        self._auto_refresh_thread = None
        self._stop_auto_refresh = threading.Event()
        
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
    
    def _format_event_for_console(self, event: DebuggerEvent) -> str:
        """Format a debugger event for console display with special tags."""
        # Define color tags and CSS classes for different event types
        event_tags = {
            DebuggerEventType.INPUT: ("[IN]", "event-input"),
            DebuggerEventType.OUTPUT: ("[OUT]", "event-output"), 
            DebuggerEventType.ERROR: ("[ERR]", "event-error"),
            DebuggerEventType.SYSTEM: ("[SYS]", "event-system"),
            DebuggerEventType.STATE_CHANGE: ("[STATE]", "event-state"),
            DebuggerEventType.BREAKPOINT_HIT: ("[BP]", "event-breakpoint"),
            DebuggerEventType.EXCEPTION: ("[EXC]", "event-exception"),
            DebuggerEventType.PROCESS_TERMINATED: ("[TERM]", "event-terminated")
        }
        
        tag, css_class = event_tags.get(event.type, ("[UNK]", "event-output"))
        timestamp = event.timestamp
        content = event.content
        
        # Format with HTML span for color coding
        return f'<span class="{css_class}">{timestamp} {tag} {content}</span>'
    
    def chat_with_ai(self, message: str, history: List[dict]) -> Tuple[List[dict], str, str]:
        """Handle chat interaction with the AI debugger."""
        try:
            if not message.strip():
                return history, "", ""
            
            # Get AI response
            ai_response = self.completion_handler.process_message(message)
            
            # Update history with OpenAI-style messages
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": ai_response})
            
            # Format tool call messages for display
            tool_call_html = self._format_tool_calls_for_display()
            
            return history, "", tool_call_html
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_msg})
            return history, "", ""
    
    def _format_tool_calls_for_display(self) -> str:
        """Format tool call messages for HTML display."""
        tool_call_messages = [msg for msg in self.chat_history if msg.get("role") == "tool_call"]
        
        if not tool_call_messages:
            return ""
        
        html_parts = []
        for msg in tool_call_messages:
            status = msg.get("status", "started")
            content = msg.get("content", "")
            
            # Determine CSS class based on status
            css_class = f"tool-call-{status}"
            
            # Format the message with proper styling
            html_part = f'''
            <div class="tool-call-message {css_class}">
                {content}
            </div>
            '''
            html_parts.append(html_part)
        
        return "\n".join(html_parts)
    
    def get_debugger_status(self) -> str:
        """Get current debugger status."""
        try:
            state = self.debugger.get_state()
            status_info = [
                f"**Debugger State:** {state.value.title()}",
                f"**Target PID:** {self.debugger.target_pid or 'None'}",
                f"**Attached:** {'Yes' if self.debugger.is_attached() else 'No'}"
            ]
            
            if self.debugger.list_breakpoints():
                bp_count = len(self.debugger.list_breakpoints())
                status_info.append(f"**Breakpoints:** {bp_count}")
            
            return "\n".join(status_info)
            
        except Exception as e:
            return f"Error getting status: {str(e)}"
    
    def get_debugger_console(self) -> str:
        """Get the current debugger console output from captured events."""
        try:
            if not self.console_events:
                return '<div style="color: #888; font-family: monospace;">No debugger events captured yet. Start debugging to see output.</div>'
            
            # Format all events for display
            formatted_events = []
            for event in self.console_events:
                formatted_events.append(self._format_event_for_console(event))
            
            # Join with line breaks and wrap in a styled container
            html_content = '<br>'.join(formatted_events)
            return f'''
            <div style="
                background-color: #1a1a1a; 
                color: #00ff00; 
                font-family: 'Courier New', monospace; 
                font-size: 12px; 
                border: 1px solid #333; 
                border-radius: 5px; 
                padding: 10px; 
                max-height: 400px; 
                overflow-y: auto; 
                white-space: pre-wrap;
                line-height: 1.4;
            ">
                {html_content}
            </div>
            '''
            
        except Exception as e:
            return f'<div style="color: #ff0000; font-family: monospace;">Error getting console output: {str(e)}</div>'
    
    def get_debugger_console_plain(self) -> str:
        """Get the current debugger console output as plain text."""
        try:
            if not self.console_events:
                return "No debugger events captured yet. Start debugging to see output."
            
            # Format all events for display as plain text
            formatted_events = []
            for event in self.console_events:
                # Define plain text tags for different event types
                event_tags = {
                    DebuggerEventType.INPUT: "[IN]",
                    DebuggerEventType.OUTPUT: "[OUT]", 
                    DebuggerEventType.ERROR: "[ERR]",
                    DebuggerEventType.SYSTEM: "[SYS]",
                    DebuggerEventType.STATE_CHANGE: "[STATE]",
                    DebuggerEventType.BREAKPOINT_HIT: "[BP]",
                    DebuggerEventType.EXCEPTION: "[EXC]",
                    DebuggerEventType.PROCESS_TERMINATED: "[TERM]"
                }
                
                tag = event_tags.get(event.type, "[UNK]")
                timestamp = event.timestamp
                content = event.content
                
                formatted_events.append(f"{timestamp} {tag} {content}")
            
            return "\n".join(formatted_events)
            
        except Exception as e:
            return f"Error getting console output: {str(e)}"
    
    def get_event_count(self) -> int:
        """Get the number of events currently stored."""
        return len(self.console_events)
    
    def start_auto_refresh(self):
        """Start auto-refresh functionality."""
        if not self._auto_refresh_enabled:
            self._auto_refresh_enabled = True
            self._stop_auto_refresh.clear()
            self._auto_refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
            self._auto_refresh_thread.start()
    
    def stop_auto_refresh(self):
        """Stop auto-refresh functionality."""
        self._auto_refresh_enabled = False
        self._stop_auto_refresh.set()
        if self._auto_refresh_thread and self._auto_refresh_thread.is_alive():
            self._auto_refresh_thread.join(timeout=1)
    
    def _auto_refresh_loop(self):
        """Background thread for auto-refresh functionality."""
        while self._auto_refresh_enabled and not self._stop_auto_refresh.is_set():
            try:
                if self.debugger.is_attached():
                    current_count = len(self.console_events)
                    if current_count != self._last_event_count:
                        self._last_event_count = current_count
                        # The UI will be updated on the next manual refresh
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"Auto-refresh error: {e}")
                time.sleep(2)
    
    def clear_debugger_console(self) -> Tuple[str, str]:
        """Clear the debugger console log."""
        try:
            # Clear the console events
            self.console_events.clear()
            return "Console cleared.", "Console cleared."
        except Exception as e:
            error_msg = f"Error clearing console: {str(e)}"
            return error_msg, error_msg
    
    def clear_chat_history(self) -> Tuple[List[dict], str, str]:
        """Clear the chat history."""
        self.completion_handler.clear_history()
        self.chat_history.clear()  # Clear tool call messages too
        return [], "", ""
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface."""
        with gr.Blocks(
            title="Debug Agent - AI-Powered Debugging Assistant",
            theme=gr.themes.Soft(),
            css="""
            .container { max-width: 1200px; margin: auto; }
            .status-box { background-color: #f0f0f0; padding: 15px; border-radius: 5px; }
            .console-box textarea { 
                background-color: #1a1a1a !important; 
                color: #00ff00 !important; 
                font-family: 'Courier New', monospace !important; 
                font-size: 12px !important;
                border: 1px solid #333 !important;
                border-radius: 5px !important; 
            }
            .console-box label {
                color: #333 !important;
            }
            /* Event type color coding */
            .event-input { color: #ffff00 !important; }  /* Yellow for input */
            .event-output { color: #00ff00 !important; } /* Green for output */
            .event-error { color: #ff0000 !important; }  /* Red for errors */
            .event-system { color: #00ffff !important; } /* Cyan for system */
            .event-state { color: #ff00ff !important; }  /* Magenta for state changes */
            .event-breakpoint { color: #ff8800 !important; } /* Orange for breakpoints */
            .event-exception { color: #ff0088 !important; } /* Pink for exceptions */
            .event-terminated { color: #880000 !important; } /* Dark red for termination */
            
            /* Tool call message styling */
            .tool-call-message {
                background-color: #f8f9fa !important;
                border-left: 4px solid #007bff !important;
                padding: 12px !important;
                margin: 8px 0 !important;
                border-radius: 6px !important;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
                font-size: 13px !important;
                line-height: 1.4 !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
            }
            .tool-call-started {
                background-color: #fff3cd !important;
                border-left-color: #ffc107 !important;
                color: #856404 !important;
            }
            .tool-call-completed {
                background-color: #d4edda !important;
                border-left-color: #28a745 !important;
                color: #155724 !important;
            }
            .tool-call-failed {
                background-color: #f8d7da !important;
                border-left-color: #dc3545 !important;
                color: #721c24 !important;
            }
            .tool-call-error {
                background-color: #f8d7da !important;
                border-left-color: #dc3545 !important;
                color: #721c24 !important;
            }
            .tool-call-container {
                margin-top: 10px !important;
                margin-bottom: 10px !important;
            }
            .tool-call-container label {
                font-weight: bold !important;
                color: #333 !important;
                margin-bottom: 8px !important;
            }
            """
        ) as interface:
            
            gr.Markdown(
                """
                # 🐛 Debug Agent
                
                An AI-powered debugging assistant that helps analyze crashes and debug applications.
               
                """,
                elem_classes=["container"]
            )
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Main chat interface
                    chatbot = gr.Chatbot(
                        label="AI Debugging Assistant",
                        height=500,
                        show_copy_button=True,
                        type='messages'
                    )
                    
                    # Custom HTML display for tool calls
                    tool_call_display = gr.HTML(
                        value="",
                        label="Tool Execution",
                        visible=True,
                        elem_classes=["tool-call-container"]
                    )
                    
                    msg = gr.Textbox(
                        label="Message",
                        placeholder="Ask the AI to help debug an application...",
                        lines=1,
                        scale=4
                    )
                    
                    with gr.Row():
                        send_btn = gr.Button("Send", variant="primary")
                        clear_btn = gr.Button("Clear Chat", variant="secondary")
                
                with gr.Column(scale=1):
                    # Status panel
                    gr.Markdown("## Debugger Status")
                    status_display = gr.Markdown(
                        value=self.get_debugger_status(),
                        elem_classes=["status-box"]
                    )
                    
                    refresh_status_btn = gr.Button("Refresh Status")
                    
                    # Debugger console panel
                    gr.Markdown("## Debugger Console")
                    console_display = gr.HTML(
                        value=self.get_debugger_console(),
                        label="CDB Input/Output",
                        elem_classes=["console-box"]
                    )
                    
                    with gr.Row():
                        refresh_console_btn = gr.Button("Refresh Console", size="sm")
                        clear_console_btn = gr.Button("Clear Console", size="sm", variant="secondary")
                        auto_refresh_toggle = gr.Checkbox(label="Auto-refresh", value=False)
            
            # Example prompts
            with gr.Row():
                gr.Markdown("### Example Prompts")
                example_buttons = [
                    gr.Button("Debug a C++ application", size="sm"),
                    gr.Button("Analyze a crash dump", size="sm"),
                    gr.Button("Help with access violation", size="sm"),
                    gr.Button("Set breakpoints", size="sm")
                ]
            
            # Event handlers
            send_btn.click(
                self.chat_with_ai,
                [msg, chatbot],
                [chatbot, msg, tool_call_display]
            )
            
            msg.submit(
                self.chat_with_ai,
                [msg, chatbot],
                [chatbot, msg, tool_call_display]
            )
            
            clear_btn.click(
                self.clear_chat_history,
                outputs=[chatbot, msg, tool_call_display]
            )
            
            refresh_status_btn.click(
                self.get_debugger_status,
                outputs=status_display
            )
            
            # Auto-refresh functionality
            def auto_refresh_console_output():
                """Auto-refresh console output when debugger is active."""
                return self.get_debugger_console()
            
            def toggle_auto_refresh(enabled):
                """Toggle auto-refresh functionality."""
                if enabled:
                    self.start_auto_refresh()
                else:
                    self.stop_auto_refresh()
                return self.get_debugger_console()
            
            # Set up auto-refresh toggle
            auto_refresh_toggle.change(
                toggle_auto_refresh,
                inputs=[auto_refresh_toggle],
                outputs=console_display
            )
            
            # Add auto-refresh that only runs when debugger is active
            def conditional_auto_refresh():
                """Auto-refresh only when debugger is attached and there are new events."""
                if self.debugger.is_attached():
                    current_count = len(self.console_events)
                    if current_count != self._last_event_count:
                        self._last_event_count = current_count
                        return self.get_debugger_console()
                return gr.update()  # No update if debugger not attached or no new events
            
            # Set up refresh button with conditional logic
            refresh_console_btn.click(
                conditional_auto_refresh,
                outputs=console_display
            )
            
            # Note: Auto-refresh is handled manually via the refresh button
            # Users can click refresh to see new events, or use the auto-refresh toggle
            # for immediate updates when toggled
            
            clear_console_btn.click(
                self.clear_debugger_console,
                outputs=[status_display, console_display]
            )
            
            # Example button handlers
            example_prompts = [
                "Help me debug my C++ application. The executable is at C:\\path\\to\\app.exe",
                "I have a crash dump file. Can you help me analyze it?",
                "My application is crashing with an access violation. What should I do?",
                "How do I set breakpoints to debug my application?"
            ]
            
            for i, btn in enumerate(example_buttons):
                btn.click(
                    lambda prompt=example_prompts[i]: ([], prompt, ""),
                    outputs=[chatbot, msg, tool_call_display]
                )
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        try:
            # Validate configuration
            config.validate()
            
            interface = self.create_interface()
            interface.launch(
                server_name=config.gradio_host,
                server_port=config.gradio_port,
                share=config.gradio_share,
                show_error=True,
                **kwargs
            )
            
        except Exception as e:
            print(f"Error launching interface: {e}")
            raise

    def _handle_tool_call(self, tool_call_info: dict):
        """Handle tool call notifications from the completion handler."""
        # Log what goes into this function
        print(f"Tool call info: {tool_call_info}")
        print(f"Tool call type: {tool_call_info['type']}")
        print(f"Tool name: {tool_call_info['tool_name']}")

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
                "status": "started"
            })
            
        elif tool_call_type == "tool_call_complete":
            # Update the tool call message with results
            result = tool_call_info["result"]
            if result.success:
                result_str = json.dumps(result.data, indent=2)
                tool_message = f"✅ **Tool completed:** `{tool_name}`\n\n**Result:**\n```json\n{result_str}\n```"
            else:
                tool_message = f"❌ **Tool failed:** `{tool_name}`\n\n**Error:** {result.error}"
            
            # Find and update the corresponding tool call message
            for i, msg in enumerate(self.chat_history):
                if (msg.get("role") == "tool_call" and 
                    msg.get("tool_name") == tool_name and 
                    msg.get("status") == "started"):
                    self.chat_history[i] = {
                        "role": "tool_call",
                        "content": tool_message,
                        "tool_name": tool_name,
                        "status": "completed" if result.success else "failed"
                    }
                    break
                    
        elif tool_call_type == "tool_call_error":
            # Update the tool call message with error
            error_msg = tool_call_info["error"]
            tool_message = f"💥 **Tool error:** `{tool_name}`\n\n**Error:** {error_msg}"
            
            # Find and update the corresponding tool call message
            for i, msg in enumerate(self.chat_history):
                if (msg.get("role") == "tool_call" and 
                    msg.get("tool_name") == tool_name and 
                    msg.get("status") == "started"):
                    self.chat_history[i] = {
                        "role": "tool_call",
                        "content": tool_message,
                        "tool_name": tool_name,
                        "status": "error"
                    }
                    break 