#!/usr/bin/env python3
"""Test script for tool call functionality."""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.gradio_interface import DebugAgentInterface

def test_tool_call_functionality():
    """Test that tool calls are properly captured and displayed."""
    print("Testing tool call functionality...")
    
    # Create interface
    interface = DebugAgentInterface()
    
    # Test tool call callback
    test_tool_call = {
        "type": "tool_call_start",
        "tool_name": "launch_application",
        "arguments": {"executable_path": "test.exe"},
        "tool_call_id": "test-123"
    }
    
    # Call the tool call handler
    interface._handle_tool_call(test_tool_call)
    
    # Check if tool call was added to history
    tool_calls = [msg for msg in interface.chat_history if msg.get("role") == "tool_call"]
    print(f"Found {len(tool_calls)} tool call messages in history")
    
    if tool_calls:
        print("Tool call message content:")
        print(tool_calls[0]["content"])
        
        # Test formatting
        html_output = interface._format_tool_calls_for_display()
        print("\nFormatted HTML output:")
        print(html_output)
        
        print("\n✅ Tool call functionality test passed!")
    else:
        print("❌ No tool call messages found in history")
        return False
    
    return True

if __name__ == "__main__":
    test_tool_call_functionality() 