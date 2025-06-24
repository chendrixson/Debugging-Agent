"""Usage examples for the Debug Agent."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from debugger.platform.windows import WindowsDebugger
from tools.attach_tool import LaunchApplicationTool
from tools.stack_tool import AnalyzeCrashTool, WaitForEventTool


def example_launch_and_analyze_crash():
    """Example of launching an app and analyzing a crash."""
    print("Example: Launch application and analyze crash")
    
    # Initialize debugger
    debugger = WindowsDebugger()
    
    # Create tools
    launch_tool = LaunchApplicationTool(debugger)
    wait_tool = WaitForEventTool(debugger)
    analyze_tool = AnalyzeCrashTool(debugger)
    
    # Example executable (you'd replace this with actual path)
    executable_path = r"C:\path\to\your\crash_test.exe"
    
    if not os.path.exists(executable_path):
        print(f"Executable not found: {executable_path}")
        print("Please compile the crash_test.cpp example or provide a valid executable path")
        return
    
    try:
        # Launch the application
        print(f"Launching {executable_path}...")
        result = launch_tool.execute(executable_path=executable_path)
        
        if result.success:
            print(f"Application launched with PID: {result.data['pid']}")
            
            # Wait for an event (crash, breakpoint, etc.)
            print("Waiting for debug event...")
            event_result = wait_tool.execute(timeout=30)
            
            if event_result.success:
                print(f"Debug event occurred: {event_result.data['event']['type']}")
                
                # If it's a crash, analyze it
                if debugger.get_state().value == "crashed":
                    print("Application crashed, analyzing...")
                    crash_result = analyze_tool.execute()
                    
                    if crash_result.success:
                        crash_data = crash_result.data
                        print(f"Crash Analysis:")
                        print(f"  Exception: {crash_data['exception_type']}")
                        print(f"  Message: {crash_data['exception_message']}")
                        print(f"  Address: {crash_data['crash_address']}")
                        print(f"  Stack frames: {len(crash_data['stack_trace'])}")
                    else:
                        print(f"Failed to analyze crash: {crash_result.error}")
            else:
                print(f"No debug event occurred: {event_result.error}")
                
        else:
            print(f"Failed to launch application: {result.error}")
            
    except Exception as e:
        print(f"Error in example: {e}")
    finally:
        # Clean up
        try:
            debugger.detach()
        except:
            pass


def example_tool_descriptions():
    """Example showing available tools and their descriptions."""
    print("Available Debug Tools:")
    print("=" * 50)
    
    # This would typically be done through the tool registry
    tools = [
        ("launch_application", "Launch an application under the debugger"),
        ("attach_to_process", "Attach to an existing process"),
        ("analyze_crash", "Analyze crash information"),
        ("get_stack_trace", "Get current stack trace"),
        ("get_current_frame", "Get the current frame (top of stack)"),
        ("wait_for_event", "Wait for debug events")
    ]
    
    for name, description in tools:
        print(f"{name}:")
        print(f"  {description}")
        print()


if __name__ == "__main__":
    print("Debug Agent Usage Examples")
    print("=" * 50)
    
    # Show available tools
    example_tool_descriptions()
    
    # Uncomment to run the crash analysis example
    # Note: This requires a compiled executable and Windows platform
    # example_launch_and_analyze_crash()
    
    print("To run the full example:")
    print("1. Compile examples/sample_programs/crash_test.cpp")
    print("2. Update the executable_path in example_launch_and_analyze_crash()")
    print("3. Uncomment the function call above") 