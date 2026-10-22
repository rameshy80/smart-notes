import gradio as gr
from faster_whisper import WhisperModel
import requests
import json

# Initialize Whisper on your RTX 5080 (using float16 for massive speedups)
print("Loading Whisper Model...")
whisper_model = WhisperModel("large-v3", device="cuda", compute_type="float16")

def process_audio(audio_path):
    if not audio_path:
        return "No audio recorded or uploaded.", ""

    # 1. Transcribe Audio
    print("Transcribing audio...")
    segments, info = whisper_model.transcribe(audio_path, beam_size=5, language="en",vad_filter= True)
    transcription = " ".join([segment.text for segment in segments])
    
    # 2. Generate SOAP Note via Local Ollama
    print("Generating SOAP Note...")
    system_prompt = (
        "You are an expert medical scribe. Convert the following unstructured medical dictation "
        "into a highly professional, structured note. Use standard medical abbreviations. "
        "Do not invent facts; if a section has no information, write N/A.\n\n"
        "Format strictly with these headers:\n"
        "CHIEF COMPLAINT:\n"
        "HISTORY OF PRESENT ILLNESS:\n"
        "Use complete story of history of present illness"
        "PAST MEDICAL HISTORY:\n"
        "SOCIAL HISTORY:\n"
        "FAMILY HISTORY:\n"
        "REVIEW OF SYSTEMS:\n"
        "OBJECTIVE:\n"
        "VITALS:\n"
        "ASSESSMENT and PLAN:\n"
        "Use professional tone and spelling.\n"
    )
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": f"{system_prompt}\n\nDictation: {transcription}",
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response_json = response.json()
        soap_note = response_json.get("response", "Error generating note.")
    except Exception as e:
        soap_note = f"Failed to connect to local LLM: {str(e)}"
        
    return transcription, soap_note

# 4. Build the Gradio UI Layout
with gr.Blocks(title="Local Medical Scribe AI") as demo:
    gr.Markdown("# 🩺 Local Medical Dictation ")
    gr.Markdown("Fully private. Processes locally on your RTX 5080.")
    
    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Record or Upload Dictation")
            submit_btn = gr.Button("Generate SOAP Note", variant="primary")
            
        with gr.Column():
            transcription_output = gr.Textbox(label="1. AI Transcription (Whisper)", lines=6, buttons=["copy"])
            soap_output = gr.Textbox(label="2. Generated SOAP Note (Llama 3)", lines=12, buttons=["copy"])
            
    submit_btn.click(
        fn=process_audio,
        inputs=[audio_input],
        outputs=[transcription_output, soap_output]
    )

if __name__ == "__main__":
    demo.launch()
