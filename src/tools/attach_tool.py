"""Tool for launching applications under the debugger."""

from typing import Dict, Any, Optional, List

# Handle imports for both package and direct execution
try:
    from src.tools.base_tool import BaseTool, ToolResult
    from src.utils.exceptions import LaunchError
except ImportError:
    from tools.base_tool import BaseTool, ToolResult
    from utils.exceptions import LaunchError


class LaunchApplicationTool(BaseTool):
    """Tool to launch an application under the debugger."""
    
    @property
    def name(self) -> str:
        return "launch_application"
    
    @property
    def description(self) -> str:
        return ( "Launch an application under the debugger to monitor for crashes and analyze behavior. "
                 "No need to attach to the process after launching.  Process is in running state after launching." )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "executable_path": {
                    "type": "string",
                    "description": "Full path to the executable to launch"
                },
                "arguments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Command line arguments for the application (optional)",
                    "default": []
                },
                "working_directory": {
                    "type": "string",
                    "description": "Working directory for the application (optional)"
                }
            },
            "required": ["executable_path"]
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool to launch an application."""
        try:
            self.validate_parameters(**kwargs)
            
            executable_path = kwargs["executable_path"]
            arguments = kwargs.get("arguments", [])
            working_directory = kwargs.get("working_directory")
            
            # Launch the process under the debugger
            pid = self.debugger.launch_process(
                executable=executable_path,
                args=arguments if arguments else None
            )
            
            return ToolResult(
                success=True,
                data={
                    "pid": pid,
                    "executable": executable_path,
                    "arguments": arguments,
                    "status": "launched",
                    "debugger_state": self.debugger.get_state().value
                },
                metadata={
                    "action": "launch_application",
                    "timestamp": self._get_timestamp()
                }
            )
            
        except LaunchError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to launch application: {str(e)}",
                metadata={"action": "launch_application"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unexpected error: {str(e)}",
                metadata={"action": "launch_application"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat()


class AttachToProcessTool(BaseTool):
    """Tool to attach to an existing process or detach from current process."""
    
    @property
    def name(self) -> str:
        return "attach_to_process"
    
    @property
    def description(self) -> str:
        return "Attach the debugger to an existing running process by PID or detach from current process"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["attach", "detach"],
                    "description": "Action to perform: attach to a process or detach from current process",
                    "default": "attach"
                },
                "pid": {
                    "type": "integer",
                    "description": "Process ID to attach to (required when action is 'attach')"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool to attach to or detach from a process."""
        try:
            self.validate_parameters(**kwargs)
            
            action = kwargs["action"]
            
            if action == "attach":
                if "pid" not in kwargs:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="PID is required when action is 'attach'",
                        metadata={"action": "attach_to_process"}
                    )
                
                pid = kwargs["pid"]
                
                # Attach to the process
                success = self.debugger.attach_to_process(pid)
                
                if success:
                    return ToolResult(
                        success=True,
                        data={
                            "pid": pid,
                            "status": "attached",
                            "debugger_state": self.debugger.get_state().value
                        },
                        metadata={
                            "action": "attach_to_process",
                            "timestamp": self._get_timestamp()
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to attach to process {pid}",
                        metadata={"action": "attach_to_process"}
                    )
            
            elif action == "detach":
                # Detach from the current process
                success = self.debugger.detach()
                
                if success:
                    return ToolResult(
                        success=True,
                        data={
                            "status": "detached",
                            "debugger_state": self.debugger.get_state().value
                        },
                        metadata={
                            "action": "detach_from_process",
                            "timestamp": self._get_timestamp()
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Failed to detach from process",
                        metadata={"action": "detach_from_process"}
                    )
            
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Invalid action: {action}. Must be 'attach' or 'detach'",
                    metadata={"action": "attach_to_process"}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error with attach/detach operation: {str(e)}",
                metadata={"action": "attach_to_process"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat() 