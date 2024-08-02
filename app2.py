from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import subprocess
import google.generativeai as genai
from gtts import gTTS
from dotenv import load_dotenv
import re
import uuid

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
    return render_template('index3.html')

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
        print(f"Transcription: {urdu_text}")  # Debugging line
    except Exception as e:
        print(f"Transcription error: {str(e)}")  # Debugging line
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500
    
    return jsonify({'transcription': urdu_text}), 200

@app.route('/bot_response', methods=['POST'])
def bot_response():
    data = request.get_json()
    if 'transcription' not in data:
        return jsonify({'error': 'No transcription provided'}), 400
    
    prompt = data['transcription']
    try:
        response = model.generate_content(prompt)
        bot_response = response.text
        print(f"Bot Response: {bot_response}")  # Debugging line

        # Preprocess the bot response text
        cleaned_bot_response = preprocess_text(bot_response)

        # Generate a unique filename using uuid
        unique_filename = f"bot_response_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join('static/audio', unique_filename)
        
        tts = gTTS(text=cleaned_bot_response, lang='ur')
        tts.save(audio_path)
    except Exception as e:
        print(f"Bot response error: {str(e)}")  # Debugging line
        return jsonify({'error': f'Bot response generation failed: {str(e)}'}), 500
    
    return jsonify({'response': bot_response, 'audio_url': audio_path}), 200

@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))

