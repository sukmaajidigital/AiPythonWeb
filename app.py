from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
import os
import speech_recognition as sr
from gtts import gTTS
from datetime import datetime
import google.generativeai as genai
import absl.logging

app = Flask(__name__)
load_dotenv()

# Konfigurasi API
absl.logging.set_verbosity(absl.logging.ERROR)
API_KEY = os.getenv("GENAI_API_KEY")
if not API_KEY:
    raise ValueError("API Key untuk Google Gemini tidak ditemukan di .env file.")
genai.configure(api_key=API_KEY)

MAX_RESPONSE_LENGTH = 150

@app.route("/")
def index():
    return "Aplikasi AI Suara Web Berjalan!"

def process_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        try:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="id-ID")
            return text.lower()
        except sr.UnknownValueError:
            return "Ngapunten, aku mboten mudeng."
        except sr.RequestError as e:
            return f"Ada masalah dengan layanan Speech-to-Text: {e}"
        except Exception as e:
            return f"Terjadi kesalahan: {e}"

@app.route("/speech-to-text", methods=["POST"])
def speech_to_text():
    if "audio" not in request.files:
        return jsonify({"error": "Audio file is required"}), 400

    audio_file = request.files["audio"]
    text = process_audio(audio_file)
    return jsonify({"text": text})

def generate_response(query):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content(contents=[{"parts": [{"text": query}]}])
        result_dict = result.to_dict() if hasattr(result, "to_dict") else None

        if result_dict and "candidates" in result_dict:
            answer = result_dict["candidates"][0]["content"]["parts"][0]["text"]
            return answer.strip()
        else:
            return "Maaf, aku belum punya jawaban untuk itu."
    except Exception as e:
        return f"Kesalahan saat memproses query: {e}"

@app.route("/generate-response", methods=["POST"])
def generate():
    data = request.json
    if "query" not in data:
        return jsonify({"error": "Query is required"}), 400

    query = data["query"]
    response = generate_response(query)
    return jsonify({"response": response})

@app.route("/text-to-speech", methods=["POST"])
def text_to_speech():
    data = request.json
    if "text" not in data:
        return jsonify({"error": "Text is required"}), 400

    text = data["text"]
    language = data.get("language", "id")
    tts = gTTS(text=text, lang=language, slow=False)
    audio_path = "response.mp3"
    tts.save(audio_path)
    return send_file(audio_path, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True)
