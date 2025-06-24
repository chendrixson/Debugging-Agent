"""Tool for controlling execution: get state, break into, or continue execution."""
from typing import Dict, Any

try:
    from src.tools.base_tool import BaseTool, ToolResult
    from src.debugger.base import DebuggerState
    from src.utils.exceptions import DebuggerError
except ImportError:
    from tools.base_tool import BaseTool, ToolResult
    from debugger.base import DebuggerState
    from utils.exceptions import DebuggerError

class ExecutionControlTool(BaseTool):
    @property
    def name(self) -> str:
        return "execution_control"

    @property
    def description(self) -> str:
        return (
            "Control execution: get_state (returns current debugger state), "
            "break_into (pause running process), or continue_execution (resume if paused)."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get_state", "break_into", "continue_execution"],
                    "description": "The execution control action to perform"
                }
            },
            "required": ["action"]
        }

    def execute(self, **kwargs) -> ToolResult:
        try:
            self.validate_parameters(**kwargs)
            action = kwargs["action"]

            if not self.debugger.is_attached():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Cannot perform action - debugger is not attached to a process",
                    metadata={"action": action, "state": self.debugger.get_state().value}
                )

            state = self.debugger.get_state()

            if action == "get_state":
                return ToolResult(
                    success=True,
                    data={"state": state.value},
                    metadata={"action": action}
                )
            elif action == "break_into":
                if state != DebuggerState.RUNNING:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Cannot break into - debugger is not running",
                        metadata={"action": action, "state": state.value}
                    )
                self.debugger.break_into()
                return ToolResult(
                    success=True,
                    data={"action": action, "status": "executed"},
                    metadata={"action": action, "timestamp": self._get_timestamp()}
                )
            elif action == "continue_execution":
                if state != DebuggerState.PAUSED:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Cannot continue - debugger is not paused",
                        metadata={"action": action, "state": state.value}
                    )
                success = self.debugger.continue_execution()
                if success:
                    return ToolResult(
                        success=True,
                        data={"action": action, "status": "executed"},
                        metadata={"action": action, "timestamp": self._get_timestamp()}
                    )
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Failed to continue execution",
                        metadata={"action": action}
                    )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown execution control action: {action}",
                    metadata={"action": action}
                )
        except DebuggerError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to {kwargs.get('action', 'control')}: {str(e)}",
                metadata={"action": kwargs.get('action', 'control')}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error during {kwargs.get('action', 'control')}: {str(e)}",
                metadata={"action": kwargs.get('action', 'control')}
            )

    def _get_timestamp(self) -> str:
        import datetime
        return datetime.datetime.now().isoformat() 