import os

# Replace this with the actual path to your FFmpeg bin folder!
FFMPEG_BIN_PATH = r"D:/ffmpeg/bin" 

if os.path.exists(FFMPEG_BIN_PATH):
    os.add_dll_directory(FFMPEG_BIN_PATH)
    os.environ["PATH"] = FFMPEG_BIN_PATH + os.path.pathsep + os.environ["PATH"]
else:
    print(f"Warning: FFmpeg bin folder not found at {FFMPEG_BIN_PATH}. torchcodec might fail.")

import requests
import re
import torch
import json
import gradio as gr
from docx import Document
from docx.shared import Pt, RGBColor
from transformers import pipeline, AutoTokenizer

# 1. Initialize Whisper Pipeline correctly on your hardware
MODEL_PATH = "whisper-medical-final"
print("Loading Whisper Model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, clean_up_tokenization_spaces=False)
whisper_pipeline = pipeline(
    "automatic-speech-recognition",
    model=MODEL_PATH,
    tokenizer=tokenizer,
    device="cuda" if torch.cuda.is_available() else "cpu"
)

def extract_headings_from_cells(doc_path):
    """Scans all tables and collects text from cells explicitly styled as Heading 6."""
    doc = Document(doc_path)
    headings = []
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if paragraph.style.name == 'Heading 6':
                        text = paragraph.text.strip()
                        if text and text not in headings:
                            headings.append(text)
    return headings

# --- BATCH TRANSCRIPTION WORKER ---
def execute_batch_transcription(audio_filepath):
    """Executes full audio transcription using clean, predictable parameter layers."""
    medical_prompt = (
        "Patient presents with acute myocardial infarction, exacerbation of COPD, "
        "and pleural effusion. Vital signs stable. Labs ordered: CBC, CMP, and troponin. "
    )
    
    try:
        raw_prompt_ids = whisper_pipeline.tokenizer.get_prompt_ids(medical_prompt)
        prompt_tensor = torch.tensor(raw_prompt_ids, dtype=torch.long).to(whisper_pipeline.device)
    except Exception as e:
        print(f"Failed to initialize prompt tokens: {e}")
        prompt_tensor = None

    punctuation_map = {
        r"\bnew paragraph\b": "\n\n",
        r"\bnew line\b": "\n",
        r"\bopen parenthesis\b": " (",
        r"\bclose parenthesis\b": ")",
        r"\bperiod\b": ".",
        r"\bcomma\b": ",",
        r"\bcolon\b": ":",
        r"\bsemi colon\b": ";",
        r"\bsemicolon\b": ";",
        r"\bquestion mark\b": "?",
        r"\bexclamation point\b": "!",
        r"\bhyphen\b": "-",
    }

    try:
        generate_kwargs = {
            "do_sample": False,
            "language": "english",
            "task": "transcribe",
            "return_timestamps": True  # Crucial flag for audio files longer than 30 seconds
        }
        
        if prompt_tensor is not None:
            generate_kwargs["prompt_ids"] = prompt_tensor

        # Run pipeline natively directly using the audio filepath string from Gradio
        result = whisper_pipeline(audio_filepath, chunk_length_s=30, generate_kwargs=generate_kwargs)
        cleaned_text = result["text"].strip()
        
        if cleaned_text:
            for pattern, punctuation in punctuation_map.items():
                cleaned_text = re.sub(pattern, punctuation, cleaned_text, flags=re.IGNORECASE)
            
            cleaned_text = re.sub(r'\s+([.,:;?!])', r'\1', cleaned_text)
            cleaned_text = re.sub(r',\s*\.', '.', cleaned_text)
            cleaned_text = re.sub(r'\.\s*\.', '.', cleaned_text)
            cleaned_text = re.sub(r':\s*\.', ':', cleaned_text)
            
            return cleaned_text
        return ""
    except Exception as e:
        print(f"Transcription Error: {e}")
        return f"Error during processing: {str(e)}"

# --- DECOUPLED GRADIO STEP FUNCTIONS ---

def step_one_transcribe(audio_path):
    """Fires Step 1: Handles Whisper processing exclusively."""
    if not audio_path:
        return "Status: No audio file provided.", "Please record audio first."
    
    transcription = execute_batch_transcription(audio_path)
    
    if not transcription or transcription.startswith("Error"):
        return f"Status: Failed. {transcription}", ""
        
    return "Status: Step 1 Complete! Review text below, then click Step 2.", transcription


def step_two_generate_document(transcription_text, doc_template):
    """Fires Step 2: Handles Llama3 parsing and document generation inline with headings.
    Forces the generated inline note text to be regular (unbolded) and solid black.
    """
    if not transcription_text or transcription_text.strip() == "":
        return "Status: Error. Dictation text is empty. Run Step 1 first.", None
    if not doc_template:
        return "Status: Error. Missing Word document template.", None

    headings = extract_headings_from_cells(doc_template.name)
    if not headings:
        return f"Status: Error. No Heading 6 style cells found in document.", None
    
    system_prompt = (
        "You are an expert medical scribe. Analyze the unstructured medical dictation and map the information "
        "strictly to the provided table headings. Return your response ONLY as a valid JSON object where the "
        "keys match the exact heading names provided, and the values contain the summarized medical text for that heading. "
        "Do not invent facts. If a heading has no relevant data in the dictation, leave its value as an empty string."
    )
    user_prompt = f"Table headings to fill: {json.dumps(headings)}\n\nDictation: {transcription_text}"
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": f"{system_prompt}\n{user_prompt}",
        "format": "json",
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response_json = response.json()
        structured_data = json.loads(response_json.get("response", "{}"))
    except Exception as e:
        return f"Status: LLM Connection Failed: {str(e)}", None
        
    print("Generating new Word document...")
    doc = Document(doc_template.name)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                # Iterate through paragraphs inside the cell to locate Heading 6 labels
                for paragraph in cell.paragraphs:
                    if paragraph.style.name == 'Heading 6':
                        original_text = paragraph.text.strip()
                        
                        # Match against the AI's structured data payload keys
                        if original_text in structured_data and structured_data[original_text]:
                            ai_text = structured_data[original_text].strip()
                            
                            # CRITICAL STACKING PREVENTION FOR INLINE RETRIES:
                            # Purge any extra text runs added past the original header label.
                            while len(paragraph.runs) > 1:
                                r_to_remove = paragraph.runs[-1]
                                r_to_remove._element.getparent().remove(r_to_remove._element)
                            
                            # Ensure the original text run is clean and explicitly contains the header title
                            if len(paragraph.runs) == 1:
                                paragraph.runs[0].text = original_text
                            
                            
                            # 2. Append the clinical AI data as an inline text run
                            capitalised_text = ai_text.capitalize()
                            value_run = paragraph.add_run(capitalised_text)
                            
                            # 3. CRITICAL STYLE COMPLIANCE: Force unbolded, regular weight black text
                            value_run.bold = False                        # Explicitly Regular (Unbolded)
                            value_run.italic = False                      # Keep it clean/upright
                            value_run.font.size = Pt(11)                  # Standard clinical body size
                            value_run.font.color.rgb = RGBColor(0, 0, 0)  # Pure Black (RGB 0,0,0)
                            
                            # 4. Strip out trailing blank paragraph gaps sitting lower in the cell boundary
                            while len(cell.paragraphs) > 1:
                                p_to_remove = cell.paragraphs[-1]
                                p_to_remove._element.getparent().remove(p_to_remove._element)
                            
    output_filename = "filled_document.docx"
    output_path = os.path.join(os.getcwd(), output_filename)
    doc.save(output_path)
    
    status_msg = f"Status: Success! Cleanly populated {len(structured_data)} table fields inline into document."
    return status_msg, output_path


# --- GRADIO UI LAYOUT ---
with gr.Blocks(title="Local Table Scribe AI") as demo:
    gr.Markdown("# 📊 Sunsara's Scribe AI")
    gr.Markdown("Two separate sequential steps to transcribe your audio, review text, and format your structured table templates.")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🛠️ Input Controls")
            doc_input = gr.File(label="1. Upload Table Template (.docx)", file_types=[".docx"])
            audio_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="2. Record Dictation File")
            
            transcribe_btn = gr.Button("Step 1: Transcribe Audio File", variant="secondary")
            make_note_btn = gr.Button("Step 2: Make Note (Generate Document)", variant="primary")
            
        with gr.Column():
            gr.Markdown("### 📝 System Outputs")
            status_output = gr.Textbox(label="System Status Logs", lines=2, value="Status: Idle. Awaiting audio dictation...")
            
            transcription_review = gr.Textbox(
                label="Transcription Output (Review / Edit here before Step 2)", 
                lines=8, 
                placeholder="Spoken text will output here after clicking Step 1..."
            )
            file_output = gr.File(label="Download Generated Word Document")

    # Interim functions to force visual loading states
    def set_loading_transcribe():
        return "Status: Running Whisper batch inference on your GPU... Please wait.", "Processing audio file channels..."

    def set_loading_note():
        return "Status: Connecting to local Llama3... Mapping text to template headings."

    # Step 1 Click Sequence
    transcribe_btn.click(
        fn=set_loading_transcribe,
        outputs=[status_output, transcription_review]
    ).then(
        fn=step_one_transcribe,
        inputs=[audio_input],
        outputs=[status_output, transcription_review]
    )
    
    # Step 2 Click Sequence
    make_note_btn.click(
        fn=set_loading_note,
        outputs=[status_output]
    ).then(
        fn=step_two_generate_document,
        inputs=[transcription_review, doc_input],
        outputs=[status_output, file_output]
    )

if __name__ == "__main__":
    demo.launch()
