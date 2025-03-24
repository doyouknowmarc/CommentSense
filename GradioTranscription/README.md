# Audio Transcription App

A Gradio-based web application for transcribing audio files (MP3 or M4A) using OpenAI's Whisper model. Perfect for transcribing interviews and long audio recordings with features like silence removal and audio chunking.

## Features

- **Multiple Audio File Support**: Process multiple MP3 or M4A files simultaneously
- **Silence Removal**: Option to remove silence from audio to reduce processing time and improve accuracy
- **Audio Chunking**: Split long audio files into manageable chunks for better processing
- **Multiple Language Support**: Supports German (de), English (en), French (fr), Spanish (es), and Italian (it)
- **Multiple Whisper Models**: Choose from various Whisper model sizes (tiny to large-v3-turbo) based on your needs
- **Detailed Output**: Get both full transcriptions and segment-wise transcriptions with timestamps
- **Download Results**: All processed files and transcripts are provided in a convenient ZIP file

## Setup

1. Clone the repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure you have ffmpeg installed on your system

## Usage

1. Run the application:
   ```bash
   python app.py
   ```
2. Open the provided local URL in your web browser
3. Upload your audio file(s)
4. Configure the settings:
   - Enable/disable silence removal
   - Enable/disable audio chunking
   - Select the Whisper model size
   - Choose the target language
5. Click "Process" to start transcription
6. View the results and download the ZIP file containing all processed files

## Settings

### Silence Removal
- **Minimum Silence Length**: 100-2000ms (default: 500ms)
- **Silence Threshold**: -70 to -30dB (default: -50dB)

### Chunking
- **Chunk Duration**: 60-3600 seconds (default: 600 seconds/10 minutes)
- **FFmpeg Path**: Path to ffmpeg executable (default: "ffmpeg")

### Transcription
- **Model Size**: Choose from tiny, base, small, medium, large, large-v2, large-v3, turbo, or large-v3-turbo
- **Language**: German (de), English (en), French (fr), Spanish (es), Italian (it)

## Output

- **Full Transcription**: Complete text of the audio file
- **Segmented Transcription**: Text segments with timestamps
- **ZIP File**: Contains:
  - Processed audio files
  - Individual transcript files
  - Combined transcript file

## Deployment on Hugging Face Spaces

1. Create a new Space on Hugging Face
2. Choose "Gradio" as the SDK
3. Upload the following files:
   - app.py
   - requirements.txt
4. The app will automatically deploy and be available at your Space's URL

## Requirements

- Python 3.7+
- ffmpeg
- See requirements.txt for Python package dependencies

## License

This project is open source and available under the MIT License.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper)
- [Gradio](https://gradio.app/)
- [FFmpeg](https://ffmpeg.org/)