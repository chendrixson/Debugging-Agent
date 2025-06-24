"""Tool for analyzing stack traces and crashes."""

from typing import Dict, Any, Optional

# Handle imports for both package and direct execution
try:
    from src.tools.base_tool import BaseTool, ToolResult
    from src.debugger.base import DebuggerState
except ImportError:
    from tools.base_tool import BaseTool, ToolResult
    from debugger.base import DebuggerState


class AnalyzeCrashTool(BaseTool):
    """Tool to analyze crash information when a process crashes."""
    
    @property
    def name(self) -> str:
        return "analyze_crash"
    
    @property
    def description(self) -> str:
        return "Analyze crash information when the debugged process crashes, providing stack trace and crash details"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute crash analysis."""
        try:
            # Check if process has crashed
            if self.debugger.get_state() != DebuggerState.CRASHED:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Process has not crashed - no crash information available",
                    metadata={"action": "analyze_crash", "state": self.debugger.get_state().value}
                )
            
            # Get crash information
            crash_info = self.debugger.analyze_crash()
            
            if crash_info:
                # Format crash information for AI analysis
                formatted_crash = {
                    "exception_type": crash_info.exception_type,
                    "exception_message": crash_info.exception_message,
                    "crash_address": crash_info.crash_address,
                    "stack_trace": [
                        {
                            "function": frame.function_name,
                            "file": frame.file_path,
                            "line": frame.line_number,
                            "module": frame.module_name,
                            "address": frame.address
                        }
                        for frame in crash_info.stack_trace
                    ],
                    "registers": crash_info.registers,
                    "modules": crash_info.modules
                }
                
                return ToolResult(
                    success=True,
                    data=formatted_crash,
                    metadata={
                        "action": "analyze_crash",
                        "timestamp": self._get_timestamp(),
                        "crash_type": crash_info.exception_type
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Could not retrieve crash information",
                    metadata={"action": "analyze_crash"}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error analyzing crash: {str(e)}",
                metadata={"action": "analyze_crash"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat()


class GetStackTraceTool(BaseTool):
    """Tool to get the current stack trace."""
    
    @property
    def name(self) -> str:
        return "get_stack_trace"
    
    @property
    def description(self) -> str:
        return "Get the current stack trace of the debugged process when paused or crashed"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute stack trace retrieval."""
        try:
            # Check if debugger is in a state where we can get stack trace
            state = self.debugger.get_state()
            if state not in [DebuggerState.PAUSED, DebuggerState.CRASHED]:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Cannot get stack trace - process is in state: {state.value}",
                    metadata={"action": "get_stack_trace", "state": state.value}
                )
            
            # Get stack trace
            stack_frames = self.debugger.get_stack_trace()
            
            formatted_stack = [
                {
                    "function": frame.function_name,
                    "file": frame.file_path,
                    "line": frame.line_number,
                    "module": frame.module_name,
                    "address": frame.address,
                }
                for frame in stack_frames
            ]
            
            return ToolResult(
                success=True,
                data={
                    "stack_frames": formatted_stack,
                    "frame_count": len(formatted_stack)
                },
                metadata={
                    "action": "get_stack_trace",
                    "timestamp": self._get_timestamp(),
                    "state": state.value
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting stack trace: {str(e)}",
                metadata={"action": "get_stack_trace"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat()


class GetCurrentFrameTool(BaseTool):
    """Tool to get the current frame (top of stack)."""
    
    @property
    def name(self) -> str:
        return "get_current_frame"
    
    @property
    def description(self) -> str:
        return "Get the current frame (top of stack) of the debugged process when paused or crashed"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute current frame retrieval."""
        try:
            # Check if debugger is in a state where we can get current frame
            state = self.debugger.get_state()
            if state not in [DebuggerState.PAUSED, DebuggerState.CRASHED]:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Cannot get current frame - process is in state: {state.value}",
                    metadata={"action": "get_current_frame", "state": state.value}
                )
            
            # Get current frame
            current_frame = self.debugger.get_current_frame()
            
            if current_frame:
                formatted_frame = {
                    "function": current_frame.function_name,
                    "file": current_frame.file_path,
                    "line": current_frame.line_number,
                    "module": current_frame.module_name,
                    "address": current_frame.address,
                }
                
                return ToolResult(
                    success=True,
                    data=formatted_frame,
                    metadata={
                        "action": "get_current_frame",
                        "timestamp": self._get_timestamp(),
                        "state": state.value
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Could not retrieve current frame information",
                    metadata={"action": "get_current_frame"}
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error getting current frame: {str(e)}",
                metadata={"action": "get_current_frame"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat()


class WaitForEventTool(BaseTool):
    """Tool to wait for debug events (crashes, breakpoints, etc.)."""
    
    @property
    def name(self) -> str:
        return "wait_for_event"
    
    @property
    def description(self) -> str:
        return "Wait for a debug event such as a crash, breakpoint hit, or process termination"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds to wait for an event (default: 30)",
                    "default": 30
                }
            },
            "required": []
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute event waiting."""
        try:
            timeout = kwargs.get("timeout", 30)
            
            # Wait for debug event
            event = self.debugger.wait_for_event(timeout)
            
            if event:
                return ToolResult(
                    success=True,
                    data={
                        "event": event,
                        "debugger_state": self.debugger.get_state().value
                    },
                    metadata={
                        "action": "wait_for_event",
                        "timestamp": self._get_timestamp(),
                        "event_type": event.get("type", "unknown")
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"No debug event occurred within {timeout} seconds",
                    metadata={
                        "action": "wait_for_event",
                        "timeout": timeout
                    }
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error waiting for event: {str(e)}",
                metadata={"action": "wait_for_event"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat() 