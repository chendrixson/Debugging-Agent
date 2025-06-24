"""Tools for stepping through code execution."""

from typing import Dict, Any, Optional

# Handle imports for both package and direct execution
try:
    from src.tools.base_tool import BaseTool, ToolResult
    from src.debugger.base import DebuggerState
    from src.utils.exceptions import DebuggerError
except ImportError:
    from tools.base_tool import BaseTool, ToolResult
    from debugger.base import DebuggerState
    from utils.exceptions import DebuggerError


class StepTool(BaseTool):
    """Tool to step through code execution with different stepping modes."""
    
    @property
    def name(self) -> str:
        return "step"
    
    @property
    def description(self) -> str:
        return "Step through code execution using different stepping modes: step_over (execute current line and stop at next), step_into (enter function calls), step_out (exit current function)"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["step_over", "step_into", "step_out"],
                    "description": "The type of stepping action to perform"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Execute stepping operation based on action type."""
        try:
            self.validate_parameters(**kwargs)
            action = kwargs["action"]

            # Check if debugger is attached for all actions
            if not self.debugger.is_attached():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Cannot perform action - debugger is not attached to a process",
                    metadata={"action": action, "state": self.debugger.get_state().value}
                )

            state = self.debugger.get_state()

            # Define required state for each action
            action_state_requirements = {
                "step_over": DebuggerState.PAUSED,
                "step_into": DebuggerState.PAUSED,
                "step_out": DebuggerState.PAUSED,
            }

            required_state = action_state_requirements.get(action)
            if required_state and state != required_state:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Cannot {action.replace('_', ' ')} - debugger is not {required_state.value}",
                    metadata={"action": action, "state": state.value}
                )

            # Execute the appropriate stepping action
            if action == "step_over":
                success = self.debugger.step_over()
            elif action == "step_into":
                success = self.debugger.step_into()
            elif action == "step_out":
                success = self.debugger.step_out()
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown stepping action: {action}",
                    metadata={"action": action}
                )

            if success:
                return ToolResult(
                    success=True,
                    data={
                        "action": action,
                        "status": "executed"
                    },
                    metadata={
                        "action": action,
                        "timestamp": self._get_timestamp()
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Failed to execute {action}",
                    metadata={"action": action}
                )

        except DebuggerError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to {kwargs.get('action', 'step')}: {str(e)}",
                metadata={"action": kwargs.get('action', 'step')}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Error during {kwargs.get('action', 'step')}: {str(e)}",
                metadata={"action": kwargs.get('action', 'step')}
            )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().isoformat() 