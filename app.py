import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from pydub import AudioSegment
from pydub.effects import pan
from werkzeug.utils import secure_filename
import time
import math

app = Flask(__name__)

# Create a directory to store converted files
UPLOAD_FOLDER = 'converted_audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def convert_to_8d(input_path, output_path):
    """
    Converts an audio file to 8D audio using pydub.
    """
    try:
        # Load the audio file
        sound = AudioSegment.from_file(input_path)

        # Convert to stereo if not already
        if sound.channels != 2:
            sound = sound.set_channels(2)

        # The 8D effect is created by panning the audio
        # back and forth between the left and right channels.
        converted_sound = AudioSegment.silent(duration=0)
        
        # We will process the sound in small chunks
        chunk_length_ms = 50 
        num_chunks = math.ceil(len(sound) / chunk_length_ms)

        for i in range(num_chunks):
            start_time = i * chunk_length_ms
            end_time = start_time + chunk_length_ms
            chunk = sound[start_time:end_time]

            # Calculate a panning value based on a sine wave for a smooth effect
            pan_value = math.sin((i / num_chunks) * 2 * math.pi)
            panned_chunk = pan(chunk, pan_value)
            
            converted_sound += panned_chunk

        # Export the processed audio
        file_extension = os.path.splitext(output_path)[1][1:]
        converted_sound.export(output_path, format=file_extension)
        return True
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

@app.route('/', methods=['GET'])
def index():
    """
    Renders the main page.
    """
    return render_template('index.html', processed_file=None, error=None)

@app.route('/convert', methods=['POST'])
def convert_audio():
    """
    Handles the file upload and conversion.
    """
    # Check if a file was uploaded
    if 'audio_file' not in request.files:
        return render_template('index.html', error="No file selected.")
    
    file = request.files['audio_file']
    
    # If the user does not select a file, the browser submits an
    # empty part without a filename.
    if file.filename == '':
        return render_template('index.html', error="No file selected.")
    
    if file:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_8D_{int(time.time())}{ext}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Convert the audio to 8D
        if convert_to_8d(input_path, output_path):
            os.remove(input_path) # Remove the original file
            return render_template('index.html', processed_file=output_filename)
        else:
            os.remove(input_path) # Clean up the uploaded file
            return render_template('index.html', error="An error occurred during conversion. Please try a different file.")

@app.route('/download/<filename>')
def download(filename):
    """
    Serves the converted audio file for download.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
