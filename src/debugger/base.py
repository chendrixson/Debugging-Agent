"""Abstract base interface for debuggers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple, Callable, Set
from dataclasses import dataclass
from enum import Enum
import threading
from datetime import datetime


class DebuggerState(Enum):
    """Debugger states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    CRASHED = "crashed"
    TERMINATED = "terminated"


class DebuggerEventType(Enum):
    """Types of debugger events."""
    INPUT = "input"  # Command sent to debugger
    OUTPUT = "output"  # Response from debugger
    ERROR = "error"  # Error message
    SYSTEM = "system"  # System message
    STATE_CHANGE = "state_change"  # Debugger state changed
    BREAKPOINT_HIT = "breakpoint_hit"  # Breakpoint was hit
    EXCEPTION = "exception"  # Exception occurred
    PROCESS_TERMINATED = "process_terminated"  # Process terminated


@dataclass
class StackFrame:
    """Represents a stack frame."""
    function_name: str
    file_path: Optional[str]
    line_number: Optional[int]
    module_name: Optional[str]
    address: Optional[str]


@dataclass
class CrashInfo:
    """Information about a crash."""
    exception_type: str
    exception_message: str
    crash_address: Optional[str]
    stack_trace: List[StackFrame]
    registers: Dict[str, str]
    memory_dump: Optional[str]
    modules: List[Dict[str, Any]]


@dataclass
class BreakpointInfo:
    """Information about a breakpoint."""
    id: int
    file_path: str
    line_number: int
    condition: Optional[str]
    enabled: bool
    hit_count: int


@dataclass
class DebuggerEvent:
    """Represents a debugger event."""
    type: DebuggerEventType
    content: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None


class BaseDebugger(ABC):
    """Abstract base class for all debuggers."""
    
    def __init__(self):
        self.state = DebuggerState.IDLE
        self.target_pid: Optional[int] = None
        self.breakpoints: Dict[int, BreakpointInfo] = {}
        self._next_breakpoint_id = 1
        self._event_callbacks: Dict[DebuggerEventType, Set[Callable[[DebuggerEvent], None]]] = {
            event_type: set() for event_type in DebuggerEventType
        }
        self._event_lock = threading.Lock()
        self.console_log: List[Tuple[str, str, str]] = []  # (timestamp, type, content)
        self._console_lock = threading.Lock()
    
    @abstractmethod
    def attach_to_process(self, pid: int) -> bool:
        """Attach debugger to a running process."""
        pass
    
    @abstractmethod
    def launch_process(self, executable: str, args: Optional[List[str]] = None) -> int:
        """Launch a process under the debugger."""
        pass
    
    @abstractmethod
    def detach(self) -> bool:
        """Detach from the current process."""
        pass
    
    @abstractmethod
    def continue_execution(self) -> bool:
        """Continue execution after a break."""
        pass
    
    @abstractmethod
    def step_over(self) -> bool:
        """Step over the next instruction."""
        pass
    
    @abstractmethod
    def step_into(self) -> bool:
        """Step into the next instruction."""
        pass
    
    @abstractmethod
    def step_out(self) -> bool:
        """Step out of the current function."""
        pass
    
    @abstractmethod
    def set_breakpoint(self, file_path: str, line_number: int, condition: Optional[str] = None) -> int:
        """Set a breakpoint at the specified location."""
        pass
    
    @abstractmethod
    def remove_breakpoint(self, breakpoint_id: int) -> bool:
        """Remove a breakpoint."""
        pass
    
    @abstractmethod
    def get_stack_trace(self) -> List[StackFrame]:
        """Get the current stack trace."""
        pass
    
    @abstractmethod
    def get_current_frame(self) -> Optional[StackFrame]:
        """Get the current frame (top of stack)."""
        pass
    
    @abstractmethod
    def get_local_variables(self, frame_index: int = 0) -> Dict[str, Any]:
        """Get local variables for the specified frame."""
        pass
    
    @abstractmethod
    def evaluate_expression(self, expression: str, frame_index: int = 0) -> Any:
        """Evaluate an expression in the specified frame context."""
        pass
    
    @abstractmethod
    def get_source_lines(self, file_path: str, start_line: int, end_line: int) -> List[str]:
        """Get source code lines from a file."""
        pass
    
    @abstractmethod
    def wait_for_event(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Wait for a debug event (breakpoint, crash, etc.)."""
        pass
    
    @abstractmethod
    def analyze_crash(self) -> Optional[CrashInfo]:
        """Analyze crash information if the process has crashed."""
        pass
    
    def get_state(self) -> DebuggerState:
        """Get the current debugger state."""
        return self.state
    
    def is_attached(self) -> bool:
        """Check if debugger is attached to a process."""
        return self.state in [DebuggerState.RUNNING, DebuggerState.PAUSED]
    
    def list_breakpoints(self) -> List[BreakpointInfo]:
        """List all breakpoints."""
        return list(self.breakpoints.values())
    
    def _generate_breakpoint_id(self) -> int:
        """Generate a unique breakpoint ID."""
        bp_id = self._next_breakpoint_id
        self._next_breakpoint_id += 1
        return bp_id 
    

    def _log_to_console(self, content: str, log_type: str = "output"):
        """Add entry to console log for UI display."""
        with self._console_lock:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.console_log.append((timestamp, log_type, content))
            
            # Keep only the last 1000 entries
            if len(self.console_log) > 1000:
                self.console_log = self.console_log[-1000:] 
    
    def register_event_callback(self, event_type: DebuggerEventType, callback: Callable[[DebuggerEvent], None]):
        """Register a callback for a specific event type.
        
        Args:
            event_type: The type of event to listen for
            callback: Function to call when event occurs. Should accept a DebuggerEvent parameter.
        """
        with self._event_lock:
            self._event_callbacks[event_type].add(callback)
    
    def unregister_event_callback(self, event_type: DebuggerEventType, callback: Callable[[DebuggerEvent], None]):
        """Unregister a callback for a specific event type.
        
        Args:
            event_type: The type of event to stop listening for
            callback: The callback function to remove
        """
        with self._event_lock:
            if callback in self._event_callbacks[event_type]:
                self._event_callbacks[event_type].remove(callback)
    
    def _fire_event(self, event_type: DebuggerEventType, content: str, data: Optional[Dict[str, Any]] = None):
        """Fire an event to all registered callbacks.
        
        Args:
            event_type: The type of event
            content: The event content/message
            data: Optional additional data for the event
        """
        event = DebuggerEvent(
            type=event_type,
            content=content,
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            data=data
        )
        
        with self._event_lock:
            callbacks = self._event_callbacks[event_type].copy()
        
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                # Log error but don't let it affect other callbacks
                print(f"Error in event callback: {e}")
    
    def _set_state(self, new_state: DebuggerState):
        """Set the debugger state and fire a state change event."""
        old_state = self.state
        self.state = new_state
        self._fire_event(
            DebuggerEventType.STATE_CHANGE,
            f"Debugger state changed from {old_state.value} to {new_state.value}",
            {"old_state": old_state.value, "new_state": new_state.value}
        ) 