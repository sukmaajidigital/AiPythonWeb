from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
import google.api_core.exceptions
import os
from dotenv import load_dotenv
from gtts import gTTS
import speech_recognition as sr
from datetime import datetime
import subprocess
from pathapp import APLIKASI  # Impor dictionary aplikasi dari pathapp.py

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
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Mendengarkan...")
        audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio, language="id-ID")
        except sr.UnknownValueError:
            return None
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

# Open Application
def open_application(app_name):
    app_path = APLIKASI.get(app_name)
    if app_path:
        try:
            subprocess.Popen([app_path], shell=True)  # Menggunakan Popen agar tidak menunggu aplikasi ditutup
            response = f"Membuka {app_name}"
            print(response)
            save_response_to_file(response)  # Simpan respons ke file
            return response
        except Exception as e:
            error_response = f"Kesalahan saat membuka {app_name}: {e}"
            print(error_response)
            save_response_to_file(error_response)  # Simpan pesan kesalahan ke file
            return error_response
    else:
        not_found_response = f"Aplikasi {app_name} tidak tersedia."
        print(not_found_response)
        save_response_to_file(not_found_response)  # Simpan pesan aplikasi tidak ditemukan ke file
        return not_found_response

# Save Response to File
def save_response_to_file(response):
    with open("responses.txt", "a") as file:
        file.write(response + "\n")

# Speak
def speak(text):
    tts = gTTS(text=text, lang="id", slow=False)
    tts.save("static/response.mp3")
    os.system("start static/response.mp3")

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

    if query_text.lower().startswith("buka"):
        app_name = query_text.replace("buka", "").strip()
        response_text = open_application(app_name)
        audio_path = text_to_speech(response_text)
        return jsonify({"response": response_text, "audio_path": audio_path})
    else:
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

@app.route("/open-application", methods=["POST"])
def open_app():
    data = request.get_json()
    app_name = data.get("app_name", "")
    if not app_name:
        return jsonify({"error": "Nama aplikasi kosong."}), 400

    response = open_application(app_name)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
