from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
import google.api_core.exceptions
import os
from dotenv import load_dotenv
from gtts import gTTS
import speech_recognition as sr
from datetime import datetime

# Load environment variables
load_dotenv()

# Flask App Initialization
app = Flask(__name__)

# Configure Google Generative AI
API_KEY = os.getenv("GENAI_API_KEY")
if not API_KEY:
    raise ValueError("API Key tidak ditemukan di file .env.")
genai.configure(api_key=API_KEY)

# Recognize Speech
def recognize_speech(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio, language="id-ID")
        except sr.UnknownValueError:
            return "Maaf, aku tidak mengerti apa yang Anda ucapkan."
        except sr.RequestError as e:
            return f"Kesalahan layanan Speech-to-Text: {e}"

# Process Query
def process_query(query):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content(contents=[{"parts": [{"text": query}]}])
        if hasattr(result, "to_dict") and "candidates" in result.to_dict():
            return result.to_dict()["candidates"][0]["content"]["parts"][0]["text"]
        return "Maaf, saya tidak dapat menemukan jawaban."
    except Exception as e:
        return f"Kesalahan saat memproses query: {e}"

# Convert Text to Speech
def text_to_speech(text, language="id"):
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        output_path = f"static/response_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        tts.save(output_path)
        return output_path
    except Exception as e:
        return f"Kesalahan Text-to-Speech: {e}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/speech-to-text", methods=["POST"])
def speech_to_text():
    if "audio" not in request.files:
        return jsonify({"error": "Tidak ada file audio yang dikirim."}), 400
    audio_file = request.files["audio"]
    file_path = f"uploads/{audio_file.filename}"
    audio_file.save(file_path)

    # Recognize speech
    text = recognize_speech(file_path)
    return jsonify({"text": text})

@app.route("/process-query", methods=["POST"])
def query():
    data = request.get_json()
    query_text = data.get("query", "")
    if not query_text:
        return jsonify({"error": "Query kosong."}), 400

    response_text = process_query(query_text)
    audio_path = text_to_speech(response_text)
    return jsonify({"response": response_text, "audio_path": audio_path})

@app.route("/text-to-speech", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "Teks kosong."}), 400

    audio_path = text_to_speech(text)
    return jsonify({"audio_path": audio_path})

@app.route("/get-audio/<filename>", methods=["GET"])
def get_audio(filename):
    return send_file(f"static/{filename}", mimetype="audio/mp3")


if __name__ == "__main__":
    app.run(debug=True)
