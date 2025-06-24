"""Windows-specific debugger implementation using cdb.exe."""

import os
import sys
import time
import subprocess
import threading
import re
import shlex
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from queue import Queue, Empty

# Handle imports for both package and direct execution
try:
    from src.debugger.base import (
        BaseDebugger, DebuggerState, StackFrame, CrashInfo, BreakpointInfo,
        DebuggerEventType, DebuggerEvent
    )
    from src.utils.exceptions import DebuggerError, AttachError, LaunchError
    from src.utils.process_utils import ProcessManager
except ImportError:
    from debugger.base import (
        BaseDebugger, DebuggerState, StackFrame, CrashInfo, BreakpointInfo,
        DebuggerEventType, DebuggerEvent
    )
    from utils.exceptions import DebuggerError, AttachError, LaunchError
    from utils.process_utils import ProcessManager


class WindowsDebugger(BaseDebugger):
    """Windows debugger implementation using cdb.exe console debugger."""
    
    def __init__(self):
        super().__init__()
        if sys.platform != "win32":
            raise DebuggerError("WindowsDebugger can only be used on Windows")
        
        self.cdb_process = None
        self.cdb_output_thread = None
        self.cdb_output_queue = Queue()
        self.cdb_command_queue = Queue()
        self.target_process = None
        self._cdb_ready = False
        self._last_output = ""
        self._cdb_process_thread_id = None
        
        # Find cdb.exe
        self.cdb_path = self._find_cdb_exe()
        if not self.cdb_path:
            raise DebuggerError("cdb.exe not found. Please install Windows SDK or Debugging Tools for Windows")
    
    def _find_cdb_exe(self) -> Optional[str]:
        """Find cdb.exe in common locations."""
        # Common locations for cdb.exe
        common_paths = [
            r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe",
            r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x86\cdb.exe",
            r"C:\Program Files\Windows Kits\10\Debuggers\x64\cdb.exe",
            r"C:\Program Files\Windows Kits\10\Debuggers\x86\cdb.exe",
            r"C:\Program Files (x86)\Windows Kits\8.1\Debuggers\x64\cdb.exe",
            r"C:\Program Files (x86)\Windows Kits\8.1\Debuggers\x86\cdb.exe",
        ]
        
        # Check if cdb is in PATH
        try:
            result = subprocess.run(["where", "cdb.exe"], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        # Check common installation paths
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _break_into_debugger(self):
        """Break into the debugger."""
        # Make sure the debugger is in the paused state.  
        if self.state == DebuggerState.PAUSED:
            return
        
        # use the inject_break.exe helper to break into the debugger.  Launch that utility and pass it the PID of the debugger process
        inject_break_path = os.path.join(os.path.dirname(__file__), "..","..","..","bin","inject_break.exe")
        subprocess.Popen([inject_break_path, str(self.target_pid)])

        # sleep for 1 seconds
        time.sleep(1)

    def break_into(self):
        """Public method to break into the debugged process (pause execution if running)."""
        self._break_into_debugger()

    def _send_cdb_command(self, command: str):
        """Queue a command to be sent to CDB by the processing thread."""
        if not self.cdb_process:
            return
        
        try:
            # Fire command queued event
            self._fire_event(DebuggerEventType.INPUT, f"Command queued: {command}")

            # Queue the command for the processing thread
            self.cdb_command_queue.put(command)
        except Exception as e:
            error_msg = f"Error queueing command: {e}"
            self._fire_event(DebuggerEventType.ERROR, error_msg)
            raise DebuggerError(f"Failed to queue command to CDB: {e}")

    def _send_cdb_command_direct(self, command: str):
        """Send a command directly to CDB from within the processing thread."""
        if not self.cdb_process or not self.cdb_process.stdin:
            return
        
        try:
            # Fire command sent event
            self._fire_event(DebuggerEventType.INPUT, f"Command sent: {command}")
            
            self.cdb_process.stdin.write(command + '\n')
            self.cdb_process.stdin.flush()

            # If the command was a g, set the state to running
            if command == "g":
                self._set_state(DebuggerState.RUNNING)
                
        except Exception as e:
            error_msg = f"Error sending command: {e}"
            self._fire_event(DebuggerEventType.ERROR, error_msg)
            raise DebuggerError(f"Failed to send command to CDB: {e}")
    
    def _read_cdb_output_with_timeout(self, timeout: float = 0.1) -> str:
        """Read a line from CDB stdout with timeout."""
        if not self.cdb_process or not self.cdb_process.stdout:
            return ""
        
        line = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                char = self.cdb_process.stdout.read(1)
                if char:
                    line += char
                    if char in ['\n', '\r', '>']:
                        break
                else:
                    time.sleep(0.01)  # Short sleep if no character
            except:
                time.sleep(0.01)
        
        return line.rstrip('\n\r') if line else ""

    def _wait_for_cdb_prompt(self, timeout: float = 10.0) -> bool:
        """Wait for CDB prompt to appear in output."""
        # Ensure this method is only called from the CDB process loop thread
        current_thread_id = threading.current_thread().ident
        if self._cdb_process_thread_id is None or current_thread_id != self._cdb_process_thread_id:
            raise RuntimeError(f"_wait_for_cdb_prompt can only be called from the CDB process loop thread")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            line = self._read_cdb_output_with_timeout(0.1)
            if line:
                self._fire_event(DebuggerEventType.OUTPUT, line)    # fire the output event for the line
                if re.search(r'([0-9]+):([0-9]+)>', line):          # if the line contains the CDB prompt, return true
                    return True
            time.sleep(0.01)
        return False

    def _cdb_process_loop(self):
        """Main CDB processing loop - handles both input and output."""
        # Cache the thread ID for _wait_for_cdb_prompt validation
        self._cdb_process_thread_id = threading.current_thread().ident
        
        # Make the pipe non-blocking
        outpipe = self.cdb_process.stdout.fileno()
        os.set_blocking(outpipe, False)
        ready_to_send_command = False

        while self.cdb_process and self.cdb_process.poll() is None:
            try:
                # Process a command, one at a time, assuming we've got a prompt which sets the ready_to_send_command flag
                if ready_to_send_command:
                    try:
                        command = self.cdb_command_queue.get_nowait()
                        self._send_cdb_command_direct(command)
                        ready_to_send_command = False
                    except Empty:
                        pass

                # Read data character by character with timeout
                line = self._read_cdb_output_with_timeout(0.1)
               
                if line:
                    self.cdb_output_queue.put(line)
                    self._last_output = line

                    # Fire output event for the line
                    self._fire_event(DebuggerEventType.OUTPUT, line)

                    # Check for the prompt, which indicates CDB readiness, and that we're ready to send a command 
                    # Use regex to check for strings like "0:004>"
                    if re.search(r'([0-9]+):([0-9]+)>', line):
                        # If we're not ready, set the ready flag and fire the ready event
                        if not self._cdb_ready:
                            self._cdb_ready = True
                            self._fire_event(DebuggerEventType.SYSTEM, "CDB debugger ready")

                        # Set the state to paused if we're in the running state
                        if self.state == DebuggerState.RUNNING:
                            self._set_state(DebuggerState.PAUSED)

                        # At a command prompt, so we're paused, and ready to send any queued commands
                        ready_to_send_command = True

                    # Check for process termination
                    if 'quit:' in line.lower() or 'terminated' in line.lower():
                        self._set_state(DebuggerState.TERMINATED)
                        self._fire_event(DebuggerEventType.PROCESS_TERMINATED, "Process terminated")
                        break
                    
                    # Check for breakpoint hits
                    if 'Breakpoint' in line and 'hit' in line:
                        # Set state to paused
                        self._set_state(DebuggerState.PAUSED)

                        # read the next line, it will contain the symbol name that was hit 
                        breakpoint_name = self.cdb_process.stdout.readline().rstrip('\n\r')
                        self._fire_event(DebuggerEventType.OUTPUT, breakpoint_name)

                        dissassembly_line = self.cdb_process.stdout.readline().rstrip('\n\r')
                        self._fire_event(DebuggerEventType.OUTPUT, dissassembly_line)

                        # Wait for CDB prompt before sending commands
                        self._wait_for_cdb_prompt()

                        # Send a k1 command to get the current source line
                        self._send_cdb_command_direct("k1")

                        # Read the header line, which contains the source line info.  Sometimes there's some extra empty lines
                        header_line = ""
                        for i in range(10):
                            header_line = self.cdb_process.stdout.readline().rstrip('\n\r')
                            if "Child-SP" in header_line:
                                break

                        self._fire_event(DebuggerEventType.OUTPUT, header_line)

                        source_line = self.cdb_process.stdout.readline().rstrip('\n\r')
                        self._fire_event(DebuggerEventType.OUTPUT, source_line)

                        # Wait for CDB prompt before completing breakpoint processing, and set the ready_to_send_command flag
                        self._wait_for_cdb_prompt()
                        ready_to_send_command = True

                        # Parse the source line to get the frame info
                        frame = self._parse_frame_from_line(source_line)
                        if frame:
                            self._fire_event(DebuggerEventType.BREAKPOINT_HIT, f"{breakpoint_name} hit at {frame.file_path}:{frame.line_number}")
                        else:
                            self._fire_event(DebuggerEventType.BREAKPOINT_HIT, f"{breakpoint_name} hit at unknown location")
                    
                    # Check for first chance excedptions, then parse out the exception type and message
                    # Format looks like this: "(36d2c.3854c): Access violation - code c0000005 (first chance)"
                    exception_match = re.search(r'\(([0-9a-fA-F]+)\.([0-9a-fA-F]+)\): (.+?) - code ([0-9a-fA-F]+) \(first chance\)', line)
                    if exception_match:
                        address, module, exception_type, code = exception_match.groups()
                        self._fire_event(DebuggerEventType.EXCEPTION, f"Exception: {exception_type} - Code: {code}")

                    
            except Exception as e:
                error_msg = f"CDB process loop error: {e}"
                self._fire_event(DebuggerEventType.ERROR, error_msg)
                break
    
    def attach_to_process(self, pid: int) -> bool:
        """Attach debugger to a running process using cdb.exe."""
        try:
            # Check if process exists
            if not ProcessManager.is_process_running(pid):
                raise AttachError(f"Process {pid} is not running")
            
            self._fire_event(DebuggerEventType.SYSTEM, f"Attaching to process {pid}...")
            
            # Start CDB attached to the process
            cdb_args = [
                self.cdb_path,
                "-p", str(pid),
                "-c", "g",  # Continue on attach
                "-lines"    # Enable source line info
            ]
            
            self._fire_event(DebuggerEventType.SYSTEM, f"Starting CDB: {' '.join(cdb_args)}")
            
            self.cdb_process = subprocess.Popen(
                cdb_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            self.target_pid = pid
            self._set_state(DebuggerState.PAUSED)   # Debugger pauses once it connects, start in that state
            
            # Start output monitoring thread
            self._start_cdb_output_thread()
            
            # Wait for CDB to be ready
            self._wait_for_cdb_ready()
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to attach to process {pid}: {e}"
            self._fire_event(DebuggerEventType.ERROR, error_msg)
            raise AttachError(error_msg)
    
    def launch_process(self, executable: str, args: Optional[List[str]] = None) -> int:
        """Launch a process normally, then attach cdb.exe to it."""
        if not os.path.exists(executable):
            raise LaunchError(f"Executable not found: {executable}")
        
        try:
            self._fire_event(DebuggerEventType.SYSTEM, f"Launching process: {executable}")

            # save off just the executable name without the path or extension into a module_name variable
            self.module_name = os.path.basename(executable).split('.')[0]
            
            # Build command line for the target process
            cmd_line = [executable]
            if args:
                cmd_line.extend(args)
            
            self._fire_event(DebuggerEventType.SYSTEM, f"Command line: {' '.join(cmd_line)}")
            
            # Launch the process normally (not under debugger initially)
            self.target_process = subprocess.Popen(
                cmd_line,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.target_pid = self.target_process.pid
            
            # Give the process a moment to start
            time.sleep(3)
            
            # Now attach CDB to the running process
            cdb_args = [
                self.cdb_path,
                "-p", str(self.target_pid),
                "-lines"    # Enable source line info
            ]
            
            self.cdb_process = subprocess.Popen(
                cdb_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            self._set_state(DebuggerState.RUNNING)
            
            # Start output monitoring thread
            self._start_cdb_output_thread()
            
            # Wait for CDB to be ready
            self._wait_for_cdb_ready()

            # Dump out symbol info
            self._send_cdb_command(".sympath")

            # Use .sympath+ to add just the path of the executable to the symbol path and reload symbols
            self._send_cdb_command(f".sympath+ {os.path.dirname(executable)}")
            self._send_cdb_command(".reload")

            # Set the debugger into source mode
            self._send_cdb_command("l+t")

            # Continue execution
            self._send_cdb_command("g")

            # Give CDB a little time to process commands
            time.sleep(1)

            return self.target_pid
            
        except Exception as e:
            error_msg = f"Failed to launch process {executable}: {e}"
            self._fire_event(DebuggerEventType.ERROR, error_msg)
            raise LaunchError(error_msg)
    
    def detach(self) -> bool:
        """Detach from the current process."""
        try:
            if self.cdb_process:
                # Check if we're in paused state, if not get into it
                current_state = self.get_state()
                if current_state != DebuggerState.PAUSED:
                    # Use break_into function to pause the process
                    self._break_into_debugger()

                # Send detach command to CDB
                self._send_cdb_command("qd")  # Quit and detach
                
                # Wait for CDB to exit
                self.cdb_process.wait(timeout=5)
                self.cdb_process = None
            
            if self.target_process:
                self.target_process = None
            
            self.target_pid = None
            self.state = DebuggerState.IDLE
            self._cdb_ready = False
            
            return True
            
        except Exception as e:
            raise DebuggerError(f"Failed to detach: {e}")
    
    def continue_execution(self) -> bool:
        """Continue execution after a break."""
        if not self.cdb_process:
            return False
        
        try:
            self._send_cdb_command_with_output("g")  # Go/Continue
            self.state = DebuggerState.RUNNING
            return True
            
        except Exception as e:
            raise DebuggerError(f"Failed to continue execution: {e}")
    
    def step_over(self) -> bool:
        """Step over the next instruction."""
        if not self.cdb_process:
            return False
        
        try:
            # Send step over command
            self._send_cdb_command_with_output("p")  # Step over
            return True
        
        except Exception as e:
            raise DebuggerError(f"Failed to step over: {e}")
    
    def step_into(self) -> bool:
        """Step into the next instruction."""
        if not self.cdb_process:
            return False
        
        try:
            # Send step into command
            self._send_cdb_command_with_output("t")  # Step into
            return True

        except Exception as e:
            raise DebuggerError(f"Failed to step into: {e}")
    
    def step_out(self) -> bool:
        """Step out of the current function."""
        if not self.cdb_process:
            return False
        
        try:
            # Send step out command
            self._send_cdb_command("gu")  # Go up (step out)
            return True
            
        except Exception as e:
            raise DebuggerError(f"Failed to step out: {e}")
    
    def set_breakpoint(self, file_path: str, line_number: int, condition: Optional[str] = None) -> int:
        """Set a breakpoint at the specified location."""
        if not self.cdb_process:
            raise DebuggerError("Debugger not attached")
        
        try:
            # Generate breakpoint ID
            bp_id = self._generate_breakpoint_id()
            
            # Set breakpoint using CDB command
            # Format: bp `filename:line`
            bp_cmd = f"bp `{file_path}:{line_number}`"
            if condition:
                bp_cmd += f" \"{condition}\""
            
            self._send_cdb_command(bp_cmd)
            
            # Store breakpoint info
            bp_info = BreakpointInfo(
                id=bp_id,
                file_path=file_path,
                line_number=line_number,
                condition=condition,
                enabled=True,
                hit_count=0
            )
            self.breakpoints[bp_id] = bp_info
            
            return bp_id
            
        except Exception as e:
            raise DebuggerError(f"Failed to set breakpoint: {e}")
    
    def set_function_breakpoint(self, function_name: str, condition: Optional[str] = None) -> int:
        """Set a breakpoint at a specific function."""
        if not self.cdb_process:
            raise DebuggerError("Debugger not attached")
        
        try:
            # Make sure the debugger is in the paused state, and save off the current state to restore it later
            current_state = self.state
            if self.state == DebuggerState.RUNNING:
                self._break_into_debugger()

            # Generate breakpoint ID
            bp_id = self._generate_breakpoint_id()
            
            # First try to find the symbol in the current module
            output = self._send_cdb_command_with_output(f"x {self.module_name}!{function_name}")
            
            if not output or "Couldn't resolve" in output:
                # If not found, try searching in all modules
                output = self._send_cdb_command_with_output(f"x *!{function_name}")
            
            # Go through all the output lines and remove any that contain a "WARNING" string
            output = '\n'.join([line for line in output.split('\n') if "WARNING" not in line])

            # If the output is empty, raise an error
            if not output:
                raise DebuggerError(f"Could not resolve function symbol: {function_name}")

            # Parse the output to get the module and function address
            # Format looks like this: "00007ff7`785222e0 simple_console!calculateStatistics (int *, int)"
            # match with a regex that pulls out the address, module, function, and parameters from that format
            match = re.search(r'([0-9a-fA-F`]+) (.+)!(.+) \((.+)\)', output)
                        
            # If we don't find a match, raise an error
            if not match:
                raise DebuggerError(f"Could not resolve function symbol: {function_name}")
            
            address, module, func, params = match.groups()
            
            # Set breakpoint using CDB command
            # Format: bp module!function
            bp_cmd = f"bp {module}!{function_name}"
            if condition:
                bp_cmd += f" \"{condition}\""
            
            output = self._send_cdb_command_with_output(bp_cmd, timeout=10)
            
            # Store breakpoint info
            bp_info = BreakpointInfo(
                id=bp_id,
                file_path=None,  # Function breakpoints don't have file/line info
                line_number=None,
                condition=condition,
                enabled=True,
                hit_count=0
            )
            self.breakpoints[bp_id] = bp_info
            
            # Restore the state if we were running, and wait for the command to get sent before returning
            if current_state == DebuggerState.RUNNING:
                self._send_cdb_command("g")
                self._wait_for_command_queue_empty()

            return bp_id
            
        except Exception as e:
            raise DebuggerError(f"Failed to set function breakpoint: {e}")
    
    def remove_breakpoint(self, breakpoint_id: int) -> bool:
        """Remove a breakpoint."""
        if breakpoint_id not in self.breakpoints:
            return False
        
        try:
            # In a full implementation, we'd need to track CDB breakpoint IDs
            # For now, we'll use bc (clear breakpoint) with the address
            bp_info = self.breakpoints[breakpoint_id]
            
            # Clear breakpoint - this is simplified
            self._send_cdb_command(f"bc `{bp_info.file_path}:{bp_info.line_number}`")
            
            del self.breakpoints[breakpoint_id]
            return True
            
        except Exception as e:
            raise DebuggerError(f"Failed to remove breakpoint: {e}")
    
    def get_stack_trace(self) -> List[StackFrame]:
        """Get the current stack trace."""
        if not self.cdb_process:
            return []
        
        try:
            # Get stack trace using CDB 'k' command
            output = self._send_cdb_command_with_output("k", timeout=60) # wait a full minute for the output
            
            frames = []
            for line in output.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                frame = self._parse_frame_from_line(line)
                if frame:
                    frames.append(frame)
            
            return frames
            
        except Exception as e:
            raise DebuggerError(f"Failed to get stack trace: {e}")
    
    def get_current_frame(self) -> Optional[StackFrame]:
        """Get the current frame (top of stack) using k1 command."""
        if not self.cdb_process:
            return None
        
        try:
            # Check if debugger is in a state where we can get stack frame
            state = self.get_state()
            if state not in [DebuggerState.PAUSED, DebuggerState.CRASHED]:
                raise DebuggerError(f"Cannot get current frame - process is in state: {state.value}")
            
            # Get current frame using CDB 'k1' command (similar to breakpoint handler)
            output = self._send_cdb_command_with_output("k1", timeout=10)
            
            # Parse the output to find the frame line
            for line in output.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Try to parse this line as a frame
                frame = self._parse_frame_from_line(line)
                if frame:
                    return frame
            
            return None
            
        except Exception as e:
            raise DebuggerError(f"Failed to get current frame: {e}")
    
    def get_local_variables(self, frame_index: int = 0) -> Dict[str, Any]:
        """Get local variables for the specified frame."""
        if not self.cdb_process:
            return {}
        
        try:
            # Get local variables using CDB 'dv' command
            output = self._send_cdb_command_with_output("dv")
            
            variables = {}
            for line in output.split('\n'):
                line = line.strip()
                if '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0].strip()
                        var_value = parts[1].strip()
                        variables[var_name] = var_value
            
            return variables
            
        except Exception as e:
            raise DebuggerError(f"Failed to get local variables: {e}")
    
    def evaluate_expression(self, expression: str, frame_index: int = 0) -> Any:
        """Evaluate an expression in the specified frame context."""
        if not self.cdb_process:
            return None
        
        try:
            # Evaluate expression using CDB '?' command
            output = self._send_cdb_command_with_output(f"? {expression}")
            
            # Parse the result (simplified)
            lines = output.strip().split('\n')
            if lines:
                result_line = lines[-1].strip()
                if 'Evaluate expression:' in result_line:
                    return result_line.split(':', 1)[1].strip()
                else:
                    return result_line
            
            return output.strip()
            
        except Exception as e:
            return f"Error evaluating expression: {e}"
    
    def get_source_lines(self, file_path: str, start_line: int, end_line: int) -> List[str]:
        """Get source code lines from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[start_line-1:end_line]
        except Exception:
            return []
    
    def wait_for_event(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Wait for a debug event (breakpoint, crash, etc.)."""
        if not self.cdb_process:
            return None
        
        try:
            # Create an event queue to receive events
            event_queue = Queue()
            
            # Define event handler
            def event_handler(event: DebuggerEvent):
                event_queue.put({
                    'type': event.type.value,
                    'content': event.content,
                    'data': event.data
                })
            
            # Register handler for relevant event types.  Don't include STATE_CHANGE, as those happen during the command queue processing
            event_types = [
                DebuggerEventType.BREAKPOINT_HIT,
                DebuggerEventType.EXCEPTION,
                DebuggerEventType.PROCESS_TERMINATED
            ]
            
            for event_type in event_types:
                self.register_event_callback(event_type, event_handler)
            
            try:
                # Wait for an event
                event = event_queue.get(timeout=timeout)
                return event
            except Empty:
                return None
            finally:
                # Unregister the event handler
                for event_type in event_types:
                    self.unregister_event_callback(event_type, event_handler)
            
        except Exception:
            return None
    
    def analyze_crash(self) -> Optional[CrashInfo]:
        """Analyze crash information if the process has crashed."""
        if not self.cdb_process or self.state != DebuggerState.CRASHED:
            return None
        
        try:
            # Get exception information
            exc_output = self._send_cdb_command_with_output(".exr -1")
            
            # Get stack trace
            stack_trace = self.get_stack_trace()
            
            # Get registers
            reg_output = self._send_cdb_command_with_output("r")
            
            # Parse crash information (simplified)
            crash_info = CrashInfo(
                exception_type="Unknown",
                exception_message=exc_output,
                crash_address="Unknown",
                stack_trace=stack_trace,
                registers={},
                memory_dump=None,
                modules=[]
            )
            
            return crash_info
            
        except Exception as e:
            raise DebuggerError(f"Failed to analyze crash: {e}")
    
    def _send_cdb_command_with_output(self, command: str, timeout: float = 2.0) -> str:
        """Send a command to CDB and return the output."""
        if not self.cdb_process:
            return ""
        
        try:
            # Clear output queue
            while not self.cdb_output_queue.empty():
                try:
                    self.cdb_output_queue.get_nowait()
                except Empty:
                    break
            
            # Send command
            self._send_cdb_command(command)
            
            # Collect output
            output_lines = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    line = self.cdb_output_queue.get(timeout=0.1)
                    output_lines.append(line)
                    
                    # Check if we got a prompt (indicating command completion)
                    if line.strip().endswith('>'):
                        break
                except Empty:
                    continue
            
            return '\n'.join(output_lines)
            
        except Exception as e:
            raise DebuggerError(f"Failed to get command output: {e}")
    
    def _get_cdb_output(self, timeout: Optional[float] = None) -> str:
        """Get output from CDB."""
        try:
            if timeout is None:
                line = self.cdb_output_queue.get()
            else:
                line = self.cdb_output_queue.get(timeout=timeout)
            return line
        except Empty:
            return ""
    
    def _start_cdb_output_thread(self):
        """Start thread to monitor CDB output."""
        if self.cdb_output_thread and self.cdb_output_thread.is_alive():
            return
        
        self.cdb_output_thread = threading.Thread(target=self._cdb_process_loop, daemon=True)
        self.cdb_output_thread.start()
    
    def _wait_for_cdb_ready(self, timeout: float = 60.0):
        """Wait for CDB to be ready."""
        start_time = time.time()
        while not self._cdb_ready and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if not self._cdb_ready:
            raise DebuggerError("CDB failed to become ready within timeout")
    
    def _wait_for_command_queue_empty(self, timeout: float = 10.0) -> bool:
        """Wait until the command queue is empty, up to the specified timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.cdb_command_queue.empty():
                return True
            time.sleep(0.1)  # Short sleep to avoid busy waiting
        
        return False
    
    def _parse_frame_from_line(self, line: str) -> Optional[StackFrame]:
        """Parse a stack frame from a CDB output line."""
        # Parse stack frame, which looks like this:
        # 000000d2`a29ff4a0 00007ff7`78522a5f     simple_console!runTestMode+0x80 [D:\Source\Debug-Agent\test_apps\simple_console\simple_console.cpp @ 74]
        # Use a regex to pull out the function name, file path, line number, and address
        match = re.search(r'([0-9a-fA-F`]+) ([0-9a-fA-F`]+)\s+(.+)!(.+) \[([^\]]+)\s+@\s+(\d+)\]', line)
        
        if match:
            stack_address, return_address, module, func, source_file, source_line = match.groups()
            return StackFrame(
                function_name=func,
                file_path=source_file,
                line_number=source_line,
                module_name=module,
                address=stack_address
            )
        
        return None  