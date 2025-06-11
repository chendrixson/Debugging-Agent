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
        return "Launch an application under the debugger to monitor for crashes and analyze behavior"
    
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
    """Tool to attach to an existing process."""
    
    @property
    def name(self) -> str:
        return "attach_to_process"
    
    @property
    def description(self) -> str:
        return "Attach the debugger to an existing running process by PID"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pid": {
                    "type": "integer",
                    "description": "Process ID to attach to"
                }
            },
            "required": ["pid"]
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool to attach to a process."""
        try:
            self.validate_parameters(**kwargs)
            
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
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error attaching to process: {str(e)}",
                metadata={"action": "attach_to_process"}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat() 