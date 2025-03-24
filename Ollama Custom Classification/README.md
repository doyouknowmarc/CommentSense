# YouTube Comment Custom Classification with Ollama

A Chrome extension that performs real-time custom classification of YouTube comments using Ollama's language models. This tool helps users understand and categorize video discussions through advanced natural language processing and custom classification categories.

## Features

- Real-time custom classification of YouTube comments using Ollama
- Side panel interface for easy access and interaction
- Visual classification indicators for each analyzed comment
- Custom classification filtering options
- Analysis summary statistics
- Comment analysis history saved to CSV

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
   The server will run locally and handle classification requests

### Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the extension directory
4. The extension icon should appear in your Chrome toolbar

## Usage

1. Navigate to any YouTube video
2. Click the extension icon to open the side panel
3. The extension will automatically analyze visible comments
4. Use the filtering options to view comments by classification
5. View the analysis summary for overall classification distribution

## Technical Details

- Backend: FastAPI server with Ollama integration
- Model: Ollama's language models for custom classification
- Frontend: Chrome Extension with Side Panel UI
- Data Storage: CSV file for analysis history

## Files

- `server.py`: FastAPI server handling comment classification
- `manifest.json`: Chrome extension configuration
- `background.js`: Extension background service worker
- `content.js`: YouTube page interaction script
- `sidepanel.html/js`: Extension UI implementation

## Security

- CORS enabled for local development
- API endpoint restricted to POST requests
- Input validation for comment analysis

## Requirements

See `requirements.txt` for a complete list of Python dependencies.