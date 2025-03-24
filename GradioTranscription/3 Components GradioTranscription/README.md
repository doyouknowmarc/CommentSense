# Audio Processing and Transcription Suite

A collection of Gradio web applications for audio processing, transcription, and file manipulation.

## Features

### 1. Audio Transcription App (audio_transcription_app.py)
- Batch transcription of multiple audio files using OpenAI's Whisper model
- Support for multiple languages (German, English, French, Spanish, Italian)
- Individual transcripts for each file
- Combined transcript with all files
- Segment-wise transcription with timestamps
- Downloadable transcript files

### 2. Audio File Splitter (audio_splitter_app.py)
- Split large audio files into smaller chunks
- Support for MP3 and M4A formats
- Customizable chunk duration
- Format conversion options
- Download processed files

### 3. Silence Removal Tool (silence_removal_app.py)
- Remove silence from audio files
- Adjustable silence detection parameters
- Preview processed audio
- Support for various audio formats

## Installation

1. Clone the repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```
3. Ensure FFmpeg is installed on your system
   - For macOS: `brew install ffmpeg`
   - For Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - For Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

## Dependencies

- Python 3.7+
- Gradio 4.0+
- OpenAI Whisper
- PyTorch 2.0+
- PyDub
- FFmpeg

## Usage

### Audio Transcription
```bash
python audio_transcription_app.py
```
- Upload one or more audio files (MP3 or M4A)
- Select the Whisper model size (tiny to large)
- Choose the transcription language
- Click "Transcribe" to process the files
- View results and download transcripts

### Audio Splitting
```bash
python audio_splitter_app.py
```
- Upload an audio file
- Set the desired chunk duration
- Process and download split files

### Silence Removal
```bash
python silence_removal_app.py
```
- Upload an audio file
- Adjust silence detection parameters
- Process and preview the result

## Notes

- The Whisper model will be downloaded on first use
- Larger model sizes provide better accuracy but require more processing time
- CPU is used by default for stability
- Processing time depends on file size and model selection