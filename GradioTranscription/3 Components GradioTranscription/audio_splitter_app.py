import gradio as gr
import os
import subprocess
import tempfile

def split_audio(audio_path, chunk_duration=600, output_format="mp3", convert_to_mp3=False, ffmpeg_path="ffmpeg"):
    try:
        if not audio_path:
            return "No file uploaded", None

        # Get the input file extension and base name
        input_ext = os.path.splitext(audio_path)[1].lower()
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        # Create a temporary directory for output files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare the output filename pattern
            output_pattern = os.path.join(temp_dir, f"{base_name}_%03d.{output_format}")
            
            # Prepare ffmpeg command based on input/output formats
            if convert_to_mp3 and input_ext == ".m4a":
                # Convert M4A to MP3 with specific bitrate
                cmd = [
                    ffmpeg_path, "-i", audio_path,
                    "-f", "segment",
                    "-segment_time", str(chunk_duration),
                    "-c:a", "libmp3lame",
                    "-b:a", "192k",
                    output_pattern
                ]
            else:
                # Simple copy for same format
                cmd = [
                    ffmpeg_path, "-i", audio_path,
                    "-f", "segment",
                    "-segment_time", str(chunk_duration),
                    "-c:a", "copy",
                    output_pattern
                ]
            
            # Execute ffmpeg command
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                return f"Error: {process.stderr}", None
            
            # Get all generated files
            output_files = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir)])
            
            # Create a zip file containing all chunks
            zip_path = f"{base_name}_chunks.zip"
            subprocess.run(["zip", "-j", zip_path] + output_files)
            
            return "Audio splitting completed successfully!", zip_path
    
    except Exception as e:
        return f"Error: {str(e)}", None

def create_interface():
    with gr.Blocks(title="Audio File Splitter") as app:
        gr.Markdown("# Audio File Splitter")
        gr.Markdown("Upload an audio file (MP3 or M4A) to split it into chunks.")
        
        with gr.Row():
            with gr.Column():
                audio_input = gr.File(
                    label="Upload Audio File (MP3 or M4A)",
                    file_types=["audio/mpeg", "audio/mp4"],
                    type="filepath"
                )
                
                chunk_duration = gr.Slider(
                    minimum=60,
                    maximum=1800,
                    value=600,
                    step=60,
                    label="Chunk Duration (seconds)"
                )
                
                output_format = gr.Radio(
                    choices=["mp3", "m4a"],
                    value="mp3",
                    label="Output Format"
                )
                
                convert_to_mp3 = gr.Checkbox(
                    label="Convert M4A to MP3 (applies only to M4A input)",
                    value=False
                )

                ffmpeg_path = gr.Textbox(
                    label="FFmpeg Path (optional)",
                    placeholder="ffmpeg",
                    value=""
                )
                
                process_btn = gr.Button("Split Audio", variant="primary")
            
            with gr.Column():
                status_output = gr.Textbox(label="Status")
                download_output = gr.File(label="Download Chunks (ZIP)")
        
        process_btn.click(
            fn=split_audio,
            inputs=[
                audio_input,
                chunk_duration,
                output_format,
                convert_to_mp3,
                ffmpeg_path
            ],
            outputs=[
                status_output,
                download_output
            ]
        )
    
    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(share=True)