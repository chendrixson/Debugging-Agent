"""Test script for debugging tools with colored output."""

import os
import sys
import time
from pathlib import Path
from colorama import init, Fore, Style

# Add src to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from tools.attach_tool import LaunchApplicationTool, AttachToProcessTool
from tools.stack_tool import AnalyzeCrashTool, WaitForEventTool
from tools.breakpoint_tool import SetBreakpointTool, RemoveBreakpointTool
from tools.variable_tool import GetVariablesTool
from tools.stack_tool import GetStackTraceTool
from debugger.factory import DebuggerFactory
from debugger.base import DebuggerEventType, DebuggerEvent

# Initialize colorama
init()

def handle_debugger_event(event: DebuggerEvent):
    """Handle debugger events with color coding."""
    if event.type == DebuggerEventType.INPUT:
        print(f"{Fore.YELLOW}[IN] {event.content}{Style.RESET_ALL}")
    elif event.type == DebuggerEventType.OUTPUT:
        print(f"{Fore.GREEN}[OUT] {event.content}{Style.RESET_ALL}")
    elif event.type == DebuggerEventType.ERROR:
        print(f"{Fore.RED}[ERR] {event.content}{Style.RESET_ALL}")
    elif event.type == DebuggerEventType.SYSTEM:
        print(f"{Fore.MAGENTA}[SYS] {event.content}{Style.RESET_ALL}")
    elif event.type == DebuggerEventType.STATE_CHANGE:
        print(f"{Fore.CYAN}[STATE] {event.content}{Style.RESET_ALL}")
    elif event.type == DebuggerEventType.BREAKPOINT_HIT:
        print(f"{Fore.BLUE}[BP] {event.content}{Style.RESET_ALL}")
    elif event.type == DebuggerEventType.EXCEPTION:
        print(f"{Fore.RED}[EXC] {event.content}{Style.RESET_ALL}")
    elif event.type == DebuggerEventType.PROCESS_TERMINATED:
        print(f"{Fore.RED}[TERM] {event.content}{Style.RESET_ALL}")

def test_debugger_tools():
    """Test the core debugging functionality using platform-agnostic tools."""
    print(f"{Fore.CYAN}[CMD] Initializing tools...{Style.RESET_ALL}")
    
    # Create debugger instance using factory
    debugger = DebuggerFactory.create_debugger()
    
    # Register event handlers
    for event_type in DebuggerEventType:
        debugger.register_event_callback(event_type, handle_debugger_event)
    
    # Create tools
    launch_tool = LaunchApplicationTool(debugger)
    attach_tool = AttachToProcessTool(debugger)
    wait_tool = WaitForEventTool(debugger)
    analyze_tool = AnalyzeCrashTool(debugger)
    set_bp_tool = SetBreakpointTool(debugger)
    remove_bp_tool = RemoveBreakpointTool(debugger)
    get_vars_tool = GetVariablesTool(debugger)
    get_stack_tool = GetStackTraceTool(debugger)
    
    try:
        # Save current working directory
        working_dir = os.getcwd()
        print(f"{Fore.CYAN}[CMD] Current working directory: {working_dir}{Style.RESET_ALL}")

        # Test 1: Launch and debug a new process
        print(f"{Fore.CYAN}[CMD] === Test 1: Launch and debug new process ==={Style.RESET_ALL}")
        
        # Example: Launch simple_console.exe from the test_apps folder
        executable_path = os.path.join(working_dir, "test_apps", "simple_console", "x64", "Debug", "simple_console.exe")
        
        print(f"{Fore.CYAN}[CMD] Launching test app from {executable_path}{Style.RESET_ALL}")
        result = launch_tool.execute(
            executable_path=executable_path,
            arguments=["test"]
        )
        
        if result.success:
            pid = result.data["pid"]
            print(f"{Fore.CYAN}[CMD] Test app launched with PID: {pid}{Style.RESET_ALL}")
            
            # Wait a moment for the process to initialize
            time.sleep(2)
            
            # Set a breakpoint (this is just an example - in reality you'd need a valid file/line)
            print(f"{Fore.CYAN}[CMD] Setting breakpoint in calculateStatistics function...{Style.RESET_ALL}")
            try:
                bp_result = set_bp_tool.execute(
                    function_name="calculateStatistics"
                )
                if bp_result.success:
                    print(f"{Fore.CYAN}[CMD] Breakpoint set with ID: {bp_result.data['breakpoint_id']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.CYAN}[CMD] Could not set breakpoint: {bp_result.error}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.CYAN}[CMD] Error setting breakpoint: {e}{Style.RESET_ALL}")
            
            # Wait for an event
            print(f"{Fore.CYAN}[CMD] Waiting for breakpoint to hit...{Style.RESET_ALL}")
            event_result = wait_tool.execute(timeout=60)
            
            if event_result.success:
                print(f"{Fore.CYAN}[CMD] Debug event occurred: {event_result.data['event']['type']}{Style.RESET_ALL}")
                
                # Get stack trace
                print(f"{Fore.CYAN}[CMD] Getting stack trace...{Style.RESET_ALL}")
                stack_result = get_stack_tool.execute()
                if stack_result.success:
                    for frame in stack_result.data['stack_frames']:
                        print(f"{Fore.CYAN}[CMD] Frame: {frame['function']} at {frame['address']} in {frame['file']} on line {frame['line']}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.CYAN}[CMD] Failed to get stack trace: {stack_result.error}{Style.RESET_ALL}")
                
                # Get local variables
                print(f"{Fore.CYAN}[CMD] Getting local variables...{Style.RESET_ALL}")
                vars_result = get_vars_tool.execute()
                if vars_result.success:
                    for var_name, var_value in vars_result.data['variables'].items():
                        print(f"{Fore.CYAN}[CMD] Variable: {var_name} = {var_value}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.CYAN}[CMD] Failed to get variables: {vars_result.error}{Style.RESET_ALL}")
            else:
                print(f"{Fore.CYAN}[CMD] No debug event occurred: {event_result.error}{Style.RESET_ALL}")
            
            # Detach from the process
            print(f"{Fore.CYAN}[CMD] Detaching from process...{Style.RESET_ALL}")
            detach_result = attach_tool.execute(action="detach")
            if detach_result.success:
                print(f"{Fore.CYAN}[CMD] Successfully detached from process{Style.RESET_ALL}")
            else:
                print(f"{Fore.CYAN}[CMD] Failed to detach: {detach_result.error}{Style.RESET_ALL}")
            
        else:
            print(f"{Fore.CYAN}[CMD] Failed to launch App: {result.error}{Style.RESET_ALL}")
        
           
    except Exception as e:
        print(f"{Fore.CYAN}[CMD] Error in test: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    test_debugger_tools() 