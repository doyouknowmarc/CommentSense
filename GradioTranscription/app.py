import gradio as gr
import warnings
import torch
import os
import whisper
import ssl
import zipfile
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import subprocess
import tempfile
import time

ssl._create_default_https_context = ssl._create_unverified_context

def process_audio(
    audio_paths,
    remove_silence=False,
    min_silence_len=500,
    silence_thresh=-50,
    enable_chunking=False,
    chunk_duration=600,
    ffmpeg_path="ffmpeg",
    model_size="large-v3-turbo",
    language="de"
):
    try:
        if not audio_paths:
            return "No files selected.", "", None

        # Clean up any existing temp directory at the start
        temp_dir = "temp_processing"
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")
            try:
                os.rmdir(temp_dir)
            except Exception as e:
                print(f"Error removing temp directory: {e}")

        # Create fresh temp directory with unique timestamp
        temp_dir = f"temp_processing_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        
        processed_files = []
        all_results = []
        all_segments = []
        all_txt_paths = []

        try:
            # Step 1: Process each audio file
            for audio_path in audio_paths:
                if not audio_path:
                    continue
                    
                current_file = audio_path
                temp_files = []
                
                # Step 1a: Split audio if chunking is enabled
                if enable_chunking:
                    base_name = os.path.splitext(os.path.basename(current_file))[0]
                    output_pattern = os.path.join(temp_dir, f"{base_name}_part_%d.mp3")
                    
                    cmd = [
                        ffmpeg_path, "-i", current_file,
                        "-f", "segment",
                        "-segment_time", str(chunk_duration),
                        "-c:a", "copy",
                        "-segment_start_number", "1",
                        output_pattern
                    ]
                    
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    chunk_files = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir) 
                                       if f.startswith(f"{base_name}_part_")])
                    temp_files.extend(chunk_files)
                else:
                    temp_files.append(current_file)
                
                # Step 1b: Remove silence if requested
                if remove_silence:
                    silence_removed_files = []
                    for file in temp_files:
                        audio = AudioSegment.from_file(file)
                        nonsilent = detect_nonsilent(
                            audio,
                            min_silence_len=min_silence_len,
                            silence_thresh=silence_thresh
                        )
                        output = AudioSegment.empty()
                        for start, end in nonsilent:
                            output += audio[start:end]
                        
                        # Save the silence-removed file
                        silence_removed_path = os.path.join(temp_dir, f"silence_removed_{os.path.basename(file)}")
                        output.export(silence_removed_path, format="mp3")
                        silence_removed_files.append(silence_removed_path)
                    processed_files.extend(silence_removed_files)
                else:
                    processed_files.extend(temp_files)

            # Step 2: Transcribe all processed files
            print(f"Loading Whisper model '{model_size}'...")
            model = whisper.load_model(model_size, device="cpu")
            
            for file in processed_files:
                print(f"Transcribing: {file}")
                warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
                
                result = model.transcribe(file, fp16=False, language=language, temperature=0.0)
                
                full_text = result["text"]
                segments = ""
                for segment in result["segments"]:
                    segments += f"[{segment['start']:.2f} - {segment['end']:.2f}]: {segment['text']}\n"
                
                # Store transcript files in temp directory
                txt_path = os.path.join(temp_dir, f"transcript_{os.path.splitext(os.path.basename(file))[0]}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("=== Full Transcription ===\n\n")
                    f.write(full_text)
                    f.write("\n\n=== Segment-wise Transcription ===\n")
                    f.write(segments)
                
                all_results.append(full_text)
                all_segments.append(segments)
                all_txt_paths.append(txt_path)
            
            # Create combined transcript file in temp directory
            combined_txt_path = os.path.join(temp_dir, "combined_transcripts.txt")
            with open(combined_txt_path, "w", encoding="utf-8") as f:
                f.write("=== Combined Transcriptions ===\n\n")
                for i, (result, segment, path) in enumerate(zip(all_results, all_segments, all_txt_paths)):
                    filename = os.path.basename(processed_files[i])
                    f.write(f"File: {filename}\n")
                    f.write("=== Full Transcription ===\n")
                    f.write(result)
                    f.write("\n\n=== Segment-wise Transcription ===\n")
                    f.write(segment)
                    f.write("\n" + "-"*50 + "\n\n")
            
            # Format display output
            combined_results = "=== File Transcriptions ===\n\n"
            combined_segments = "=== File Segments ===\n\n"
            for i, (result, segment) in enumerate(zip(all_results, all_segments)):
                filename = os.path.basename(processed_files[i])
                combined_results += f"File: {filename}\n{result}\n\n"
                combined_segments += f"File: {filename}\n{segment}\n\n"
            
            # Create ZIP with all processed files and transcripts
            zip_path = f"processed_files_and_transcripts_{int(time.time())}.zip"
            cleanup_files = processed_files.copy()

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in processed_files:
                    if os.path.exists(file):
                        zipf.write(file, os.path.basename(file))
                for txt_file in all_txt_paths:
                    if os.path.exists(txt_file):
                        zipf.write(txt_file)
                if os.path.exists(combined_txt_path):
                    zipf.write(combined_txt_path)

            # Cleanup files after ZIP creation
            for file in cleanup_files:
                if os.path.exists(file):
                    os.remove(file)
            for txt_file in all_txt_paths:
                if os.path.exists(txt_file):
                    os.remove(txt_file)
            if os.path.exists(combined_txt_path):
                os.remove(combined_txt_path)

            # Clean up temp directory
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(temp_dir)

            return combined_results, combined_segments, zip_path

        except Exception as inner_e:
            print(f"Error during processing: {inner_e}")
            raise inner_e

    except Exception as e:
        print(f"Error in process_audio: {e}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            try:
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(temp_dir)
            except:
                pass
        return f"Error: {str(e)}", "", None

def create_interface():
    with gr.Blocks(title="Interview Audio Processing App") as app:
        gr.Markdown("""
        # Audio Processing App
        Upload audio files (MP3 or M4A) for processing and transcription.\\
        Intended use case: transcription of interviews.
        """)
        with gr.Row():
            with gr.Column():
                audio_input = gr.File(
                    label="Upload Audio Files",
                    file_count="multiple",
                    type="filepath"
                )
                
                with gr.Group():
                    gr.Markdown("###  Silence Removal Settings")
                    gr.Markdown(" Default settings are working very well. Silence removal helps to reduce hallucination.")
                    remove_silence = gr.Checkbox(
                        label="Remove Silence",
                        value=False
                    )
                    
                    min_silence_len = gr.Slider(
                        minimum=100,
                        maximum=2000,
                        value=500,
                        step=100,
                        label="Minimum Silence Length (ms)",
                        visible=False
                    )
                    silence_thresh = gr.Slider(
                        minimum=-70,
                        maximum=-30,
                        value=-50,
                        step=5,
                        label="Silence Threshold (dB)",
                        visible=False
                    )
                
                with gr.Group():
                    gr.Markdown("###  Chunking Settings")
                    gr.Markdown(" Chunking reduces the load on the model. 10min chunks work really good.")
                    enable_chunking = gr.Checkbox(
                        label="Enable Chunking",
                        value=False
                    )
                    chunk_duration = gr.Slider(
                        minimum=60,
                        maximum=3600,
                        value=600,
                        step=60,
                        label="Chunk Duration (seconds)",
                        visible=False
                    )
                    ffmpeg_path = gr.Textbox(
                        label="FFmpeg Path",
                        value="ffmpeg",
                        placeholder="Path to ffmpeg executable",
                        visible=False
                    )
                
                with gr.Group():
                    gr.Markdown("###  Transcription Settings")
                    gr.Markdown(" tiny is the fastest, but the worst quality. Large-v3-turbo is the best, but slower.")
                    model_size = gr.Dropdown(
                        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "turbo", "large-v3-turbo"],
                        value="large-v3-turbo",
                        label="Whisper Model Size"
                    )
                    language = gr.Dropdown(
                        choices=["de", "en", "fr", "es", "it"],
                        value="de",
                        label="Language"
                    )
                
                process_btn = gr.Button("Process", variant="primary")
                delete_btn = gr.Button("Delete Everything", variant="stop")
            
            with gr.Column():
                full_transcription = gr.Textbox(label="Full Transcription", lines=15)
                segmented_transcription = gr.Textbox(label="Segmented Transcription", lines=15)
                download_output = gr.File(label="Download Processed Files and Transcripts (ZIP)")
        
        def update_silence_controls(remove_silence):
            return {
                min_silence_len: gr.update(visible=remove_silence),
                silence_thresh: gr.update(visible=remove_silence),
                full_transcription: gr.update(value=""),
                segmented_transcription: gr.update(value=""),
                download_output: gr.update(value=None)
            }
        
        def update_chunking_controls(enable_chunking):
            return {
                chunk_duration: gr.update(visible=enable_chunking),
                ffmpeg_path: gr.update(visible=enable_chunking),
                full_transcription: gr.update(value=""),
                segmented_transcription: gr.update(value=""),
                download_output: gr.update(value=None)
            }
        
        remove_silence.change(
            fn=update_silence_controls,
            inputs=[remove_silence],
            outputs=[
                min_silence_len,
                silence_thresh,
                full_transcription,
                segmented_transcription,
                download_output
            ]
        )
        
        enable_chunking.change(
            fn=update_chunking_controls,
            inputs=[enable_chunking],
            outputs=[
                chunk_duration,
                ffmpeg_path,
                full_transcription,
                segmented_transcription,
                download_output
            ]
        )
        
        process_btn.click(
            fn=process_audio,
            inputs=[
                audio_input,
                remove_silence,
                min_silence_len,
                silence_thresh,
                enable_chunking,
                chunk_duration,
                ffmpeg_path,
                model_size,
                language,
            ],
            outputs=[
                full_transcription,
                segmented_transcription,
                download_output,
            ]
        )
    
        # Add cleanup function
        def cleanup_files():
            try:
                # Clean up temp directories
                temp_dirs = [d for d in os.listdir('.') if d.startswith('temp_processing')]
                for temp_dir in temp_dirs:
                    if os.path.exists(temp_dir):
                        for file in os.listdir(temp_dir):
                            file_path = os.path.join(temp_dir, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        os.rmdir(temp_dir)
                
                # Clean up ZIP files
                zip_files = [f for f in os.listdir('.') if f.startswith('processed_files_and_transcripts_')]
                for zip_file in zip_files:
                    if os.path.exists(zip_file):
                        os.remove(zip_file)
                
                # Clean up transcript files
                transcript_files = [f for f in os.listdir('.') if f.startswith('transcript_')]
                for transcript_file in transcript_files:
                    if os.path.exists(transcript_file):
                        os.remove(transcript_file)
                
                # Return updates for all output fields
                return {
                    full_transcription: gr.update(value="All temporary files have been deleted."),
                    segmented_transcription: gr.update(value=""),
                    download_output: gr.update(value=None)
                }
            except Exception as e:
                return {
                    full_transcription: gr.update(value=f"Error during cleanup: {str(e)}"),
                    segmented_transcription: gr.update(value=""),
                    download_output: gr.update(value=None)
                }

        # Update the delete button click handler
        delete_btn.click(
            fn=cleanup_files,
            inputs=[],
            outputs=[
                full_transcription,
                segmented_transcription,
                download_output
            ]
        )
    
    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(share=False)