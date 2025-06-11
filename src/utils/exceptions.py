"""Custom exceptions for the debug agent."""


class DebugAgentError(Exception):
    """Base exception for debug agent errors."""
    pass


class DebuggerError(DebugAgentError):
    """Error related to debugger operations."""
    pass


class ProcessError(DebugAgentError):
    """Error related to process operations."""
    pass


class AttachError(DebuggerError):
    """Error when attaching to a process."""
    pass


class LaunchError(DebuggerError):
    """Error when launching a process."""
    pass


class BreakpointError(DebuggerError):
    """Error related to breakpoint operations."""
    pass


class AIError(DebugAgentError):
    """Error related to AI completion operations."""
    pass


class ToolError(DebugAgentError):
    """Error related to tool execution."""
    pass 