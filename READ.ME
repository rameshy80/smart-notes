# Sunsara's Scribe AI

A local Gradio app for transcribing medical dictation, reviewing the transcript, and filling a Word document template using a local Llama 3 model.

## Overview

This project does the following:

- Uses a local Whisper model for audio transcription
- Lets the user review and edit transcription text
- Sends the transcript to a local Ollama/Llama 3 model
- Maps the result to matching Word table headings
- Saves a filled `.docx` document

## Important model note

This app is configured to use a locally downloaded Whisper model:

- Model folder expected: `whisper-medical-final`
- Local path is configured in code with `MODEL_PATH = "whisper-medical-final"`

This means the software is designed to run without an online Whisper API. If you want to use an online Whisper service instead, the transcription code must be changed and configured to call that external service.

## Requirements

- Windows 10 or Windows 11
- Python 3.10+
- FFmpeg installed and available in `bin`
- Ollama installed and running locally
- Local Llama 3 model downloaded:
  - `ollama pull llama3`
- Python packages:
  - `torch`
  - `transformers`
  - `gradio`
  - `python-docx`
  - `requests`

## Setup

1. Download and place the Whisper model locally.
   - Example folder: `whisper-medical-final`
   - If needed, change `MODEL_PATH` in the script to the correct folder path.

2. Install FFmpeg.
   - Set `FFMPEG_BIN_PATH` in the script to the FFmpeg `bin` folder.
   - Example:
     ```powershell
     FFMPEG_BIN_PATH = r"D:/ffmpeg/bin"
     ```

3. Install Ollama and download the local model:
   ```powershell
   ollama pull llama3
   ```

4. Install Python dependencies:
   ```powershell
   pip install torch transformers gradio python-docx requests
   ```

5. Run the app:
   ```powershell
   python app2.py
   ```

6. Open the local Gradio URL shown in the terminal.

## How it works

1. Audio is transcribed with Whisper using the local model.
2. The transcript is displayed for review.
3. The text is sent to Ollama via:
   - `http://localhost:11434/api/generate`
4. The LLM uses the document headings from the Word template to structure the output.
5. The filled document is saved as:
   - `filled_document.docx`

## Word template requirement

The template document must contain tables whose cells are labeled using a heading style, typically:

- Heading 6

The app scans the Word file for heading-based cells and maps generated medical content to those fields.

## Local vs online Whisper

This project is currently built for local Whisper use.

To use an online Whisper service instead, you would need to:

- replace or supplement the local `pipeline(...)` transcription call
- configure API keys or service endpoints
- adjust model loading and transcription logic

The current code does not do that automatically.

## Troubleshooting

- If FFmpeg is missing, transcription may fail or output may be incomplete.
- If the Whisper model folder is not found, confirm the path and model name.
- If Ollama is not running, the document-generation step will fail.
- If the template has no Heading 6 cells, the app may not populate the document correctly.
- If Python reports an error like `os.path.pathsep`, update it to `os.pathsep` in the script.

## Notes

- This app is intended for local processing and testing.
- Generated clinical content should still be reviewed carefully before use.
- The app is designed for a local environment and does not depend on cloud transcription by default.

## File structure

Typical layout:

```text
smart notes/
├── app2.py
├── READ.me
├── whisper-medical-final/   # local Whisper model folder
├── filled_document.docx     # generated output
└── template.docx            # your document template
```

## License

This project is for local use in development and workflow testing. Please check your organization’s privacy, compliance, and clinical documentation requirements before using it in a live clinical process.