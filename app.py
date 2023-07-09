from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, session
import os
from werkzeug.utils import secure_filename
import json

import data_loader
from conversation import Conversation
from data_loader import ask_your_model, load_document

app = Flask(__name__)
UPLOAD_FOLDER = 'static/text'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xlsx', 'csv', 'eml'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)


@app.route('/')
def home():
    # query = "What should you do if a customer is angry?"
    # data_loader.ask_your_model(query)
    return render_template('chat.html')


def get_persona(persona_type):
    # The base path for all persona files.
    base_path = "static/persona"

    # The path to the persona file.
    # Note: we're assuming all persona files are named <persona_type>.json
    # and located in the base_path directory.
    persona_file_path = os.path.join(base_path, f"{persona_type}.json")

    # Check if the file exists. If it does, load it. If not, load a default persona.
    if os.path.isfile(persona_file_path):
        with open(persona_file_path) as file:
            return json.load(file)
    else:
        # Default to 'business' persona if the specified persona_type doesn't exist.
        with open(os.path.join(base_path, "business.json")) as file:
            return json.load(file)


@app.route("/get_persona", methods=["POST"])
def get_persona_endpoint():
    persona_type = request.json['persona_type']
    persona = get_persona(persona_type)

    # store the current persona in the session
    session['persona'] = persona

    return jsonify({"persona": persona})


@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    message = data.get('message')
    persona_template = data.get('persona_template')  # Get the persona_template from the request

    if persona_template is None:  # Add this check
        persona_template = session.get('persona', None)
    # if persona_template is None:
    #     get_persona('business')

    response = ask_your_model(message, persona_template)  # Pass the persona_template to ask_your_model
    return jsonify({'response': response})


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload_file", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        load_document(filename)
        return jsonify({'success': True})


@app.route('/upload_folder', methods=['POST'])
def upload_folder():
    # get the "files" parameter from the request (this is how the files are sent from the JavaScript)
    files = request.files.getlist('file')

    # iterate through each file
    for file in files:
        # you can save each file to the server, or process them in any way you need.
        # Here's an example that saves the files to a directory named 'uploads' on the server
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        load_document(filename)

    # return a response
    return jsonify(status='success', message='Folder uploaded successfully')


if __name__ == '__main__':
    app.run()
