import gradio as gr
import warnings
import torch
import os
import whisper
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def transcribe_audio(audio_paths, model_size="medium", language="de"):
    try:
        all_results = []
        all_segments = []
        all_txt_paths = []

        # Load Whisper model once for all files
        print(f"Loading Whisper model '{model_size}'...")
        model = whisper.load_model(model_size, device="cpu")  # For stability, using CPU

        for audio_path in audio_paths:
            if not audio_path:
                continue

            print(f"Processing file: {audio_path}")
            # Suppress specific warnings
            warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

            # Perform transcription
            result = model.transcribe(audio_path, fp16=False, language=language, temperature=0.0)

            # Format the output
            full_text = result["text"]
            segments = ""
            for segment in result["segments"]:
                segments += f"[{segment['start']:.2f} - {segment['end']:.2f}]: {segment['text']}\n"

            # Create individual transcript file
            txt_path = f"transcript_{os.path.splitext(os.path.basename(audio_path))[0]}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("=== Full Transcription ===\n\n")
                f.write(full_text)
                f.write("\n\n=== Segment-wise Transcription ===\n")
                f.write(segments)

            all_results.append(full_text)
            all_segments.append(segments)
            all_txt_paths.append(txt_path)

        # Create combined transcript file
        combined_txt_path = "combined_transcripts.txt"
        with open(combined_txt_path, "w", encoding="utf-8") as f:
            f.write("=== Combined Transcriptions ===\n\n")
            for i, (result, segment, path) in enumerate(zip(all_results, all_segments, all_txt_paths)):
                filename = os.path.basename(audio_paths[i])
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
            filename = os.path.basename(audio_paths[i])
            combined_results += f"File: {filename}\n{result}\n\n"
            combined_segments += f"File: {filename}\n{segment}\n\n"

        return combined_results, combined_segments, combined_txt_path

    except Exception as e:
        return f"Error: {str(e)}", "", None

def create_interface():
    with gr.Blocks(title="Audio Transcription App") as app:
        gr.Markdown("# Audio Transcription App")
        gr.Markdown("Upload audio files (MP3 or M4A) to transcribe them using Whisper.")

        with gr.Row():
            with gr.Column():
                audio_input = gr.File(
                    label="Upload Audio Files",
                    file_count="multiple",
                    type="filepath"
                )

                model_size = gr.Dropdown(
                    choices=["tiny", "base", "small", "medium", "large"],
                    value="medium",
                    label="Whisper Model Size"
                )
                language = gr.Dropdown(
                    choices=["de", "en", "fr", "es", "it"],
                    value="de",
                    label="Language"
                )
                transcribe_btn = gr.Button("Transcribe", variant="primary")

            with gr.Column():
                full_transcription = gr.Textbox(label="Full Transcription", lines=15)
                segmented_transcription = gr.Textbox(label="Segmented Transcription", lines=15)
                transcript_download = gr.File(label="Download Transcript")

        transcribe_btn.click(
            fn=transcribe_audio,
            inputs=[
                audio_input,
                model_size,
                language,
            ],
            outputs=[
                full_transcription,
                segmented_transcription,
                transcript_download,
            ]
        )

    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(share=True)