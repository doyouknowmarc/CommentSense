import os
import subprocess
import sys
import urllib.request
import ssl

# Disable SSL verification (use with caution)
ssl._create_default_https_context = ssl._create_unverified_context 

def convert_video_to_mp3(input_path, output_path=None):
    """
    Convert video (MP4 or MOV) to MP3 using FFmpeg directly
    
    Parameters:
    -----------
    input_path : str
        Path to the input video file (MP4 or MOV)
    output_path : str, optional
        Path for the output MP3 file
    
    Returns:
    --------
    str or None
        Path to the converted MP3 file, or None if conversion fails
    """
    # Validate input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} does not exist.")
        return None
    
    # If no output path is specified, create one
    if output_path is None:
        directory = os.path.dirname(input_path)
        filename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(directory, f"{filename}.mp3")
    
    try:
        # Construct FFmpeg command
        ffmpeg_command = [
            'ffmpeg',
            '-i', input_path,     # Input file
            '-vn',                # Ignore video track
            '-acodec', 'libmp3lame',  # Use MP3 codec
            '-q:a', '2',          # Audio quality (0-9, lower is better)
            output_path
        ]
        
        # Run the FFmpeg command
        result = subprocess.run(
            ffmpeg_command, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        print(f"Successfully converted {input_path} to {output_path}")
        return output_path
    
    except subprocess.CalledProcessError as e:
        print("Conversion failed. Error details:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def batch_convert(input_directory, output_directory=None):
    """
    Convert all MP4 and MOV files in a directory to MP3
    
    Parameters:
    -----------
    input_directory : str
        Directory containing video files
    output_directory : str, optional
        Directory to save MP3 files
    
    Returns:
    --------
    list
        List of converted file paths
    """
    # Ensure input directory exists
    if not os.path.isdir(input_directory):
        print(f"Error: {input_directory} is not a valid directory")
        return []
    
    # Use input directory as output if not specified
    if output_directory is None:
        output_directory = input_directory
    else:
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
    
    # List to store converted files
    converted_files = []
    
    # Iterate through video files
    for filename in os.listdir(input_directory):
        if filename.lower().endswith(('.mp4', '.mov')):
            input_path = os.path.join(input_directory, filename)
            output_filename = os.path.splitext(filename)[0] + '.mp3'
            output_path = os.path.join(output_directory, output_filename)
            
            # Attempt conversion
            converted_file = convert_video_to_mp3(input_path, output_path)
            if converted_file:
                converted_files.append(converted_file)
    
    return converted_files

def main():
    # path to the video 
    input_path = "" # Add the path to the video file here
    
    # Check if input is a directory or a file
    if os.path.isdir(input_path):
        print(f"Converting all MP4 and MOV files in directory: {input_path}")
        converted_files = batch_convert(input_path)
        print(f"Converted {len(converted_files)} files")
    else:
        print(f"Converting single file: {input_path}")
        convert_video_to_mp3(input_path)

if __name__ == "__main__":
    main()