import gradio as gr
import speech_recognition as sr
import requests
import fitz  # PyMuPDF
from datetime import datetime
import os

chat_history = []

# ✅ Resume PDF analyzer
def analyze_resume(file_path):
    try:
        doc = fitz.open(file_path)
        resume_text = ""
        for page in doc:
            resume_text += page.get_text()
        return resume_text.strip()[:2000]
    except Exception as e:
        return f"❌ Error reading resume: {str(e)}"

# ✅ Voice to text
def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        return text
    except Exception as e:
        return f"❌ Voice recognition error: {str(e)}"

# ✅ Ollama AI reply via FAST API call
def ask_ollama(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json().get("response", "❌ No response from model.")
    except Exception as e:
        return f"❌ API error: {str(e)}"

# ✅ Chat handler
def handle_chat(user_input, resume_file, audio_input):
    if audio_input:
        user_input = transcribe_audio(audio_input)

    if resume_file:
        resume_text = analyze_resume(resume_file)
        user_input = f"My resume says: {resume_text[:500]}\n\n{user_input}"

    response = ask_ollama(user_input)

    chat_history.append(f"👤 You: {user_input}")
    chat_history.append(f"🤖 Bot: {response}")

    return "\n".join(chat_history)

# ✅ Export chat
def export_chat():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    txt_filename = f"chat_{now}.txt"
    pdf_filename = f"chat_{now}.pdf"

    content = "\n".join(chat_history)

    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(content)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), content, fontsize=11)
    doc.save(pdf_filename)
    doc.close()

    return f"✅ Exported as {txt_filename} and {pdf_filename}"

# ✅ Gradio UI
with gr.Blocks(css="""
body {
  background: linear-gradient(-45deg, #6c5ce7, #a29bfe, #8e44ad, #9b59b6);
  background-size: 400% 400%;
  animation: gradientBG 10s ease infinite;
  font-family: 'Poppins', sans-serif;
}
@keyframes gradientBG {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
.gr-markdown h2 {
  text-align: center;
  font-size: 2rem;
  color: white;
  margin-bottom: 1rem;
  font-weight: bold;
}
button {
  transition: 0.3s ease;
}
button:hover {
  transform: scale(1.05);
  background-color: #dedde5c6 !important;
  color: black !important;
}
.file-upload, .audio-upload {
  transition: transform 0.2s ease;
}
.file-upload:hover, .audio-upload:hover {
  transform: scale(1.05);
}
""") as ui:

    gr.Markdown("## 🤖 Resume Screener Bot")

    with gr.Row():
        msg = gr.Textbox(label="💬 Ask a question about your resume or job")
        resume = gr.File(label="📄 Upload your Resume (PDF)", file_types=[".pdf"], elem_classes=["file-upload"])
        mic = gr.Audio(label="🎤 Voice Input (.wav only)", type="filepath", elem_classes=["audio-upload"])

    with gr.Row():
        submit_btn = gr.Button("🚀 Submit")
        export_btn = gr.Button("📤 Export Chat")

    chat_output = gr.Textbox(label="📝 Chat History", lines=20)

    submit_btn.click(handle_chat, [msg, resume, mic], chat_output)
    export_btn.click(export_chat, inputs=[], outputs=chat_output)

# ✅ Render-compatible launch
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    ui.launch(server_name="0.0.0.0", server_port=port)
