"""Gradio web interface for the debug agent."""

import gradio as gr
import sys
import time
from typing import List, Tuple, Optional

# Handle imports for both package and direct execution
try:
    from src.debugger.factory import DebuggerFactory
    from src.ai.tool_registry import ToolRegistry
    from src.ai.completion_handler import CompletionHandler
    from src.utils.config import config
    from src.utils.exceptions import DebugAgentError
except ImportError:
    from debugger.factory import DebuggerFactory
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
        
        # Chat history for UI
        self.chat_history: List[dict] = []
    
    def chat_with_ai(self, message: str, history: List[dict]) -> Tuple[List[dict], str]:
        """Handle chat interaction with the AI debugger."""
        try:
            if not message.strip():
                return history, ""
            
            # Get AI response
            ai_response = self.completion_handler.process_message(message)
            
            # Update history with OpenAI-style messages
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": ai_response})
            
            return history, ""
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_msg})
            return history, ""
    
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
        """Get the current debugger console output."""
        try:
            if hasattr(self.debugger, 'get_console_output'):
                return self.debugger.get_console_output()
            else:
                return "Console output not available for this debugger platform."
        except Exception as e:
            return f"Error getting console output: {str(e)}"
    
    def clear_debugger_console(self) -> Tuple[str, str]:
        """Clear the debugger console log."""
        try:
            if hasattr(self.debugger, 'clear_console_log'):
                self.debugger.clear_console_log()
                return "Console cleared.", "Console cleared."
            else:
                return "Console clear not available for this debugger platform.", "Console clear not available for this debugger platform."
        except Exception as e:
            error_msg = f"Error clearing console: {str(e)}"
            return error_msg, error_msg
    
    def clear_chat_history(self) -> Tuple[List[dict], str]:
        """Clear the chat history."""
        self.completion_handler.clear_history()
        return [], ""
    
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
            """
        ) as interface:
            
            gr.Markdown(
                """
                # 🐛 Debug Agent
                
                An AI-powered debugging assistant that helps analyze crashes and debug applications.
                
                **Getting Started:**
                1. Ask the AI to help debug an application (e.g., "Help me debug my application at C:\\path\\to\\app.exe")
                2. The AI will launch the application under the debugger
                3. If the application crashes, the AI will automatically analyze the crash
                4. Get insights and suggestions for fixing the issues
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
                    
                    msg = gr.Textbox(
                        label="Message",
                        placeholder="Ask the AI to help debug an application...",
                        lines=2
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
                    console_display = gr.Textbox(
                        value=self.get_debugger_console(),
                        label="CDB Input/Output",
                        lines=15,
                        max_lines=15,
                        interactive=False,
                        show_copy_button=True,
                        elem_classes=["console-box"]
                    )
                    
                    with gr.Row():
                        refresh_console_btn = gr.Button("Refresh Console", size="sm")
                        clear_console_btn = gr.Button("Clear Console", size="sm", variant="secondary")
            
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
                [chatbot, msg]
            )
            
            msg.submit(
                self.chat_with_ai,
                [msg, chatbot],
                [chatbot, msg]
            )
            
            clear_btn.click(
                self.clear_chat_history,
                outputs=[chatbot, msg]
            )
            
            refresh_status_btn.click(
                self.get_debugger_status,
                outputs=status_display
            )
            
            refresh_console_btn.click(
                self.get_debugger_console,
                outputs=console_display
            )
            
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
                    lambda prompt=example_prompts[i]: ([], prompt),
                    outputs=[chatbot, msg]
                )
            
            # Set up periodic refresh for console output
            # Create a timer that refreshes the console every 2 seconds when debugger is active
            def auto_refresh_console():
                """Auto-refresh console output periodically."""
                while True:
                    time.sleep(2)  # Refresh every 2 seconds
                    if self.debugger.is_attached():
                        try:
                            # This will be handled by the frontend refresh mechanism
                            pass
                        except:
                            pass
            
            # Note: Auto-refresh handled manually via refresh buttons
            # Users can manually refresh status and console using the refresh buttons
        
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