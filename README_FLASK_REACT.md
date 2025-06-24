# Debug Agent - Flask + React Version

A modern, AI-powered debugging assistant built with Flask backend and React frontend.

## Features

- 🤖 **AI-Powered Debugging**: Uses OpenAI GPT models to analyze crashes and debug applications
- 🔄 **Real-time Updates**: WebSocket-based real-time console output and status updates
- 💬 **Interactive Chat**: Natural language interface for debugging assistance
- 🖥️ **Modern UI**: Clean, responsive React interface with Tailwind CSS
- 🐛 **Windows Debugging**: Native Windows debugging support via CDB/WinDbg
- 📊 **Live Status**: Real-time debugger status and process information
- 🎨 **Color-coded Console**: Different colors for different types of debugger events

## Architecture

```
Debug-Agent/
├── backend/                    # Flask API server
│   ├── app.py                 # Main Flask application
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API and WebSocket services
│   │   └── utils/             # Utility functions
│   ├── package.json           # Node.js dependencies
│   └── vite.config.js         # Vite configuration
├── src/                       # Core Python logic (existing)
└── run_flask_debug_agent.py   # Flask backend runner
```

## Prerequisites

### Backend Requirements
- Python 3.8+
- Windows OS (for debugging support)
- OpenAI API key

### Frontend Requirements
- Node.js 16+
- npm or yarn

## Installation

### 1. Setup Environment

```bash
# Create .env file with your configuration
python run_flask_debug_agent.py --setup
```

Edit the `.env` file with your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo-preview
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## Running the Application

### Option 1: Separate Terminals

**Terminal 1 - Backend:**
```bash
python run_flask_debug_agent.py
```

**Terminal 2 - Frontend:**
```bash
# Windows
start_frontend.bat

# Unix/Linux/Mac
./start_frontend.sh
```

### Option 2: Using Scripts

**Windows:**
```bash
# Start backend
python run_flask_debug_agent.py

# In another terminal, start frontend
start_frontend.bat
```

**Unix/Linux/Mac:**
```bash
# Start backend
python run_flask_debug_agent.py

# In another terminal, start frontend
chmod +x start_frontend.sh
./start_frontend.sh
```

## Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **WebSocket**: ws://localhost:5000

## Usage

### 1. Chat Interface
- Ask the AI to help debug your application
- Example prompts:
  - "Help me debug my C++ application"
  - "Analyze a crash dump file"
  - "Help with access violation"
  - "Set breakpoints to debug"

### 2. Debugger Console
- View real-time debugger output
- Color-coded events for different types:
  - 🟡 Yellow: Input commands
  - 🟢 Green: Output responses
  - 🔴 Red: Errors
  - 🔵 Cyan: System messages
  - 🟣 Magenta: State changes
  - 🟠 Orange: Breakpoints
  - 🟣 Pink: Exceptions

### 3. Status Panel
- Real-time debugger status
- Process information
- Breakpoint count
- Connection status

## API Endpoints

### Chat
- `POST /api/chat` - Send message to AI
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/clear` - Clear chat history

### Debugger
- `GET /api/debugger/status` - Get debugger status

### Console
- `GET /api/console/events` - Get console events
- `POST /api/console/clear` - Clear console

### WebSocket Events
- `debugger_event` - Real-time debugger events
- `tool_call_update` - Tool execution updates

## Development

### Backend Development
```bash
cd backend
python app.py
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Building for Production
```bash
cd frontend
npm run build
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_BASE_URL` | OpenAI API base URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4-turbo-preview` |
| `FLASK_HOST` | Flask host | `127.0.0.1` |
| `FLASK_PORT` | Flask port | `5000` |
| `FLASK_DEBUG` | Flask debug mode | `true` |

### Command Line Options

```bash
python run_flask_debug_agent.py --help
```

Options:
- `--setup` - Create .env template file
- `--host HOST` - Host to bind to (default: 127.0.0.1)
- `--port PORT` - Port to bind to (default: 5000)
- `--debug` - Enable debug mode

## Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check if OpenAI API key is set
   - Ensure all Python dependencies are installed
   - Check if port 5000 is available

2. **Frontend won't start**
   - Ensure Node.js is installed
   - Run `npm install` in the frontend directory
   - Check if port 3000 is available

3. **WebSocket connection issues**
   - Ensure backend is running on port 5000
   - Check firewall settings
   - Verify CORS configuration

4. **Debugger not working**
   - Ensure you're on Windows
   - Install pywin32: `pip install pywin32`
   - Check if CDB/WinDbg is available

### Logs

Backend logs are displayed in the terminal where you run the Flask server.
Frontend logs are available in the browser's developer console.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the existing issues
3. Create a new issue with detailed information

## Migration from Gradio Version

If you're migrating from the Gradio version:

1. The core Python logic remains the same
2. The new interface provides better real-time updates
3. The UI is more modern and responsive
4. WebSocket support enables live debugging feedback

The Flask + React version is a complete rewrite of the UI layer while maintaining full compatibility with your existing debugger and AI components. 