"""OpenAI completion handler for AI-powered debugging."""

import json
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI

# Handle imports for both package and direct execution
try:
    from src.utils.config import config
    from src.utils.exceptions import AIError
    from src.ai.tool_registry import ToolRegistry
except ImportError:
    from utils.config import config
    from utils.exceptions import AIError
    from ai.tool_registry import ToolRegistry


class CompletionHandler:
    """Handles OpenAI completions with tool calling for debugging."""
    
    def __init__(self, debugger, tool_registry: ToolRegistry):
        self.debugger = debugger
        self.tool_registry = tool_registry
        self.client = OpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        self.conversation_history: List[Dict[str, Any]] = []
        self.tool_call_callback: Optional[Callable] = None
        self._initialize_system_prompt()
    
    def set_tool_call_callback(self, callback: Callable):
        """Set a callback function to be called when tools are executed."""
        self.tool_call_callback = callback
    
    def _initialize_system_prompt(self):
        """Initialize the system prompt for debugging assistance."""
        system_prompt = """
You are an expert debugging assistant with access to debugging tools. Your goal is to help users debug applications by:

1. Launching applications under the debugger
2. Monitoring for crashes and exceptions
3. Analyzing crash information and stack traces
4. Providing insights and suggestions for fixing issues
5. Walking through debugging steps systematically

Available debugging tools:
{tool_descriptions}

When a user wants to debug an application:
1. First launch it using the launch_application tool
2. If a crash occurs, analyze it using analyze_crash and get_stack_trace
3. If you need to wait for a specific event, use wait_for_event and tell the user what to do next in the app.

Always explain what you're doing and why. Be thorough in your analysis and provide concrete steps for resolution."""

        tool_descriptions = "\n".join([
            f"- {name}: {desc}" 
            for name, desc in self.tool_registry.get_tool_descriptions().items()
        ])
        
        self.conversation_history = [{
            "role": "system",
            "content": system_prompt.format(tool_descriptions=tool_descriptions)
        }]
    
    def process_message(self, user_message: str) -> str:
        """Process a user message and return AI response."""
        try:
            # Add user message to conversation
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Get completion with tool calling
            response = self.client.chat.completions.create(
                model=config.openai_model,
                messages=self.conversation_history,
                tools=self.tool_registry.get_openai_functions(),
                tool_choice="auto",
                temperature=0.1  # Lower temperature for more deterministic debugging
            )
            
            message = response.choices[0].message
            
            # Handle tool calls if present
            if message.tool_calls:
                return self._handle_tool_calls(message)
            else:
                # Regular text response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content
                })
                return message.content
                
        except Exception as e:
            raise AIError(f"Error processing message: {str(e)}")
    
    def _handle_tool_calls(self, message) -> str:
        """Handle tool calls from the AI."""
        # Add assistant message with tool calls
        self.conversation_history.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in message.tool_calls
            ]
        })
        
        # Execute each tool call
        tool_results = []
        for tool_call in message.tool_calls:
            try:
                # Parse tool arguments
                args = json.loads(tool_call.function.arguments)
                
                # Notify callback about tool call start
                if self.tool_call_callback:
                    self.tool_call_callback({
                        "type": "tool_call_start",
                        "tool_name": tool_call.function.name,
                        "arguments": args,
                        "tool_call_id": tool_call.id
                    })
                
                # Execute tool
                result = self.tool_registry.execute_tool(
                    tool_call.function.name,
                    **args
                )
                
                # Format result for AI
                if result.success:
                    tool_output = json.dumps(result.data, indent=2)
                else:
                    tool_output = f"Error: {result.error}"
                
                # Notify callback about tool call completion
                if self.tool_call_callback:
                    self.tool_call_callback({
                        "type": "tool_call_complete",
                        "tool_name": tool_call.function.name,
                        "result": result,
                        "tool_call_id": tool_call.id
                    })
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": tool_output
                })
                
            except Exception as e:
                error_msg = f"Error executing tool: {str(e)}"
                
                # Notify callback about tool call error
                if self.tool_call_callback:
                    self.tool_call_callback({
                        "type": "tool_call_error",
                        "tool_name": tool_call.function.name,
                        "error": str(e),
                        "tool_call_id": tool_call.id
                    })
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": error_msg
                })
        
        # Add tool results to conversation
        self.conversation_history.extend(tool_results)
        
        # Get follow-up response from AI
        try:
            follow_up = self.client.chat.completions.create(
                model=config.openai_model,
                messages=self.conversation_history,
                tools=self.tool_registry.get_openai_functions(),
                tool_choice="auto",
                temperature=0.1
            )
            
            follow_up_message = follow_up.choices[0].message
            
            # Check for additional tool calls
            if follow_up_message.tool_calls:
                return self._handle_tool_calls(follow_up_message)
            else:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": follow_up_message.content
                })
                return follow_up_message.content
                
        except Exception as e:
            return f"Tool execution completed, but error getting follow-up: {str(e)}"
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """Clear conversation history but keep system prompt."""
        self._initialize_system_prompt()
    
    def add_context(self, context: str):
        """Add additional context to the conversation."""
        self.conversation_history.append({
            "role": "system",
            "content": f"Additional context: {context}"
        }) 