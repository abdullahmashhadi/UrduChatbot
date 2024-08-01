from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import subprocess
import google.generativeai as genai
from gtts import gTTS
from dotenv import load_dotenv
import re

app = Flask(__name__)

# Configure the API key from an environment variable
load_dotenv()
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

def preprocess_text(text):
    # Remove asterisks and any other unwanted characters or formatting
    cleaned_text = re.sub(r'[*_]', '', text)
    return cleaned_text

@app.route('/')
def index():
    return render_template('index2.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Save the file temporarily
    audio_file_path = 'uploaded_audio2.mp3'
    file.save(audio_file_path)
    
    # Transcribe the audio file to text using Whisper command line
    try:
        subprocess.run(["whisper", audio_file_path, "--model", "base", "--language", "ur"], check=True)
        
        # Read the generated transcription file
        transcription_file_path = audio_file_path.replace(".mp3", ".txt")
        with open(transcription_file_path, 'r', encoding='utf-8') as f:
            urdu_text = f.read().strip()
    except Exception as e:
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500
    
   
    prompt = urdu_text
    try:
        response = model.generate_content(prompt)
        bot_response = response.text
        cleaned_bot_response = preprocess_text(bot_response)
    except Exception as e:
        return jsonify({'error': f'Gemini API call failed: {str(e)}'}), 500


    tts_audio_path = os.path.join('static', 'audio', 'bot_response1.mp3')
    try:
        tts = gTTS(text=cleaned_bot_response, lang='ur')
        tts.save(tts_audio_path)
    except Exception as e:
        return jsonify({'error': f'TTS generation failed: {str(e)}'}), 500

    return jsonify({
        'transcription': urdu_text,
        'response': cleaned_bot_response,
        'audio_url': tts_audio_path
    }), 200

@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)


if __name__ == '__main__':
    app.run(debug=True)

