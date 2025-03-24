# YouTube Comment Sentiment Analyzer with DistilBERT

A Chrome extension that performs real-time sentiment analysis on YouTube comments using DistilBERT (Bidirectional Encoder Representations from Transformers). This tool helps users understand the emotional tone of video discussions through advanced natural language processing.

## Features

- Real-time sentiment analysis of YouTube comments using DistilBERT
- Side panel interface for easy access and interaction
- Visual sentiment indicators for each analyzed comment
- Sentiment filtering options (All, Positive, Neutral, Negative)
- Analysis summary statistics
- Comment analysis history saved to CSV

## Installation

### Server Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python server.py
   ```
   The server will run on `http://localhost:8001`

### Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the extension directory
4. The extension icon should appear in your Chrome toolbar

## Usage

1. Navigate to any YouTube video
2. Click the extension icon to open the side panel
3. The extension will automatically analyze visible comments
4. Use the radio buttons to filter comments by sentiment
5. View the analysis summary for overall sentiment distribution

## Technical Details

- Backend: FastAPI server with Hugging Face Transformers
- Model: DistilBERT (fine-tuned for sentiment analysis)
- Frontend: Chrome Extension with Side Panel UI
- Data Storage: CSV file for analysis history

## Files

- `server.py`: FastAPI server handling sentiment analysis
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

