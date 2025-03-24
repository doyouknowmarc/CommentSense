import gradio as gr
import os
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def remove_silence(input_file, min_silence_len=500, silence_thresh=-50):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)
        
        # Detect non-silent parts
        nonsilent = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
        output = AudioSegment.empty()

        # Concatenate non-silent parts
        for start, end in nonsilent:
            output += audio[start:end]

        # Generate output filename
        processed_path = f"processed_{os.path.basename(input_file)}"
        output.export(processed_path, format="mp3")
        return processed_path
    except Exception as e:
        return str(e)

def create_interface():
    with gr.Blocks(title="Audio Silence Removal") as app:
        gr.Markdown("# Audio Silence Removal Tool")
        gr.Markdown("Upload an audio file to remove silence. Adjust the parameters to fine-tune the silence detection.")

        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(
                    label="Upload Audio File",
                    type="filepath"
                )
                min_silence_len = gr.Slider(
                    minimum=100,
                    maximum=2000,
                    value=500,
                    step=100,
                    label="Minimum Silence Length (ms)"
                )
                silence_thresh = gr.Slider(
                    minimum=-70,
                    maximum=-30,
                    value=-50,
                    step=5,
                    label="Silence Threshold (dB)"
                )
                process_btn = gr.Button("Process", variant="primary")

            with gr.Column():
                output_audio = gr.Audio(label="Processed Audio", type="filepath")
                error_message = gr.Textbox(label="Status/Error", interactive=False)

        process_btn.click(
            fn=remove_silence,
            inputs=[
                audio_input,
                min_silence_len,
                silence_thresh
            ],
            outputs=[
                output_audio
            ]
        )

    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(share=True)