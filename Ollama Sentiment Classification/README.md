# YouTube Comment Sentiment Analysis with Ollama

A Chrome extension that analyzes YouTube comments' sentiment using Ollama's language models. The extension provides real-time sentiment analysis directly on YouTube pages through a convenient side panel interface.

## Features

- Real-time sentiment analysis of YouTube comments
- Integration with Ollama's language models
- Side panel interface for easy access
- Detailed sentiment reasoning for each analysis
- Support for video transcript context
- Analysis history tracking

## Installation

### Prerequisites

1. Install Ollama on your system
2. Make sure Ollama is running on your system

### Server Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python server.py
   ```
   The server will run locally on port 8002 and handle sentiment analysis requests.

### Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the extension directory
4. The extension icon should appear in your Chrome toolbar

## Usage

1. Navigate to any YouTube video
2. Click the extension icon to open the side panel
3. The extension will automatically analyze comments as you browse
4. View sentiment analysis results and reasoning in the side panel

## Technical Details

- Backend: FastAPI server with Ollama integration
- Model: Ollama's language models for sentiment analysis
- Frontend: Chrome Extension with Side Panel UI
- Data Storage: CSV file for analysis history

## Files

- `server.py`: FastAPI server handling sentiment analysis
- `manifest.json`: Chrome extension configuration
- `background.js`: Extension background service worker
- `content.js`: YouTube page interaction script
- `sidepanel.html/js`: Extension UI implementation

## Requirements

See `requirements.txt` for a complete list of Python dependencies.