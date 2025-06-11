# Debug Agent

An AI-powered debugging assistant that helps analyze crashes and debug applications across platforms. Uses OpenAI-style completion endpoints with specialized debugging tools.

## Project Structure

```
debug-agent/
├── README.md
├── requirements.txt
├── setup.py
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── ui/
│   │   ├── __init__.py
│   │   └── gradio_interface.py # Gradio UI components
│   ├── debugger/
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract debugger interface
│   │   ├── python_debugger.py # Python-specific debugging (pdb)
│   │   ├── native_debugger.py # Native code debugging
│   │   └── platform/
│   │       ├── __init__.py
│   │       ├── windows.py     # Windows debugging APIs
│   │       ├── linux.py       # Linux/ptrace implementation
│   │       └── macos.py       # macOS-specific implementation
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base_tool.py       # OpenAI tool interface base
│   │   ├── attach_tool.py     # Attach to process
│   │   ├── breakpoint_tool.py # Breakpoint management
│   │   ├── step_tool.py       # Step execution (over/into/out)
│   │   ├── source_tool.py     # Source code retrieval
│   │   ├── variables_tool.py  # Variable inspection
│   │   ├── stack_tool.py      # Stack trace analysis
│   │   └── memory_tool.py     # Memory inspection
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── completion_handler.py # OpenAI API integration
│   │   ├── tool_registry.py   # Tool registration system
│   │   └── prompt_templates.py # AI prompts for debugging
│   └── utils/
│       ├── __init__.py
│       ├── process_utils.py   # Process discovery/management
│       ├── config.py          # Configuration management
│       └── exceptions.py      # Custom exceptions
└── examples/
    ├── sample_programs/       # Test programs to debug
    └── usage_examples.py
```

## Features

- **AI-Powered Debugging**: Uses OpenAI completion API with specialized debugging tools
- **Cross-Platform Support**: Windows (primary), Linux, and macOS
- **Crash Analysis**: Automatically analyze crashes and provide insights
- **Process Management**: Launch, attach to, and monitor applications
- **Interactive UI**: Web-based Gradio interface for debugging sessions

## Initial Focus

The first implementation focuses on Windows native debugging with the following scenario:
1. Launch an application through the debugger
2. Monitor for crashes
3. Automatically analyze crash dumps and provide AI-powered insights
4. Suggest potential fixes and debugging strategies

## Installation

```bash
pip install -e .
```

## Usage

```bash
debug-agent
```

This launches the Gradio web interface where you can:
- Specify an application to launch and monitor
- Get AI-powered crash analysis
- Interact with the debugger through natural language

## Requirements

- Python 3.8+
- Windows (for initial implementation)
- OpenAI API key
- Windows SDK (for native debugging support) 