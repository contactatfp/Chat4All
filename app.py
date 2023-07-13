from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, session
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
import json
from models import db, User, NPC
import data_loader
from conversation import Conversation
from data_loader import load_document
import forms
from forms import LoginForm, RegistrationForm
# Add this inside your create_app function
from pgen import pgen, persona_form

from langchain.prompts import PromptTemplate
from langchain.prompts import load_prompt
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from flask import session


# app = Flask(__name__)

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

    db.init_app(app)

    with app.app_context():
        app.register_blueprint(pgen)

    return app



app = create_app()
# app.register_blueprint(pgen)

UPLOAD_FOLDER = 'static/text'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xlsx', 'csv', 'eml'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
# db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

migrate = Migrate(app, db)

with open('config.json') as f:
    config = json.load(f)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
chat_history = []
TEMPLATE = "tutor"


# def create_tables():
#     db.create_all()


@app.route('/')
def home():
    # query = "What should you do if a customer is angry?"
    # data_loader.ask_your_model(query)
    # create_tables()
    return render_template('home.html')


# @app.route('/')
# def index():
#
#     create_tables()
#     return render_template('home.html')


@app.route('/ask', methods=['POST'])
def ask_your_model(query, persona_template):
    from app import get_persona
    # If persona_template is None, default to 'business'
    if persona_template is None:
        persona_template = get_persona('sales_coach_inbound')

    prompt = PromptTemplate(
        input_variables=['input'],
        template=persona_template['template']
    )
    # chain = LLMChain(llm=llm, prompt=prompt)
    # Run the chain only specifying the input variable.
    # retriever = embedded_docs().as_retriever(search_kwargs={"k": 5})
    # qa = RetrievalQA.from_llm(llm=OpenAI(), retriever=retriever)

    qa = ConversationalRetrievalChain.from_llm(
        ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo-16k", openai_api_key=config['openai_api_key']),
        data_loader.embedded_docs().as_retriever(), memory=memory)
    # result = qa({"question": query, "chat_history": chat_history})
    result = qa(prompt.format(input=query))
    return result['answer']


@app.route('/api_docs', methods=['GET', 'POST'])
def api_docs():
    return render_template('api_docs.html')

    # print(result["answer"])
    # print("******************************")
    # print(chain.run(query))
    # answer = chain.run(query)

from pgen import PersonaForm
@app.route('/characters')
def characters():
    persona_files = os.listdir('static/persona')
    persona_files = [file.split('.')[0].upper() for file in persona_files]

    # Create an instance of the form
    persona_gen = PersonaForm()

    temp = {
        'BUSINESS': 'img/business exec2.png',
        'SALES COACH OUTBOUND': 'img/sales_coach_npc3.png',
        'SALES COACH INBOUND': 'img/sales_coach_npc7.png',
        'TUTOR': 'img/tutor_npc5.png',
        'BUSINESS2': "Hello, I'm Market Maven! With my comprehensive knowledge of market analysis, I'm ready to provide you data-driven insights. Let's navigate the competitive landscape and uncover opportunities together!",
        'SALES COACH OUTBOUND2': "Hi, I'm Sales Coach Sal! I specialize in enhancing sales communication and performance. By reviewing your previous emails and crafting impactful responses, I'll help you build stronger relationships with your clients. With me, every conversation becomes an opportunity to excel in your sales journey!",
        'SALES COACH INBOUND2': "Greetings, I'm Sales Coach Sam! I bring a wealth of knowledge in sales strategies and client interaction. Allow me to guide you through your past emails and shape your future correspondences for maximum impact. Together, let's hit your sales targets!",
        'TUTOR2': "Hello, I'm Tutor Tim! I excel in transforming complex lessons into easy-to-understand concepts. With your data and my expertise, I'll quiz you on past lessons and help you ace that upcoming test. Let's make learning engaging and effective!"

    }

    # Now you have a list of NPC objects in `npcs`

    # description =  {
    #     'BUSINESS': business,
    #     'SALES COACH OUTBOUND': 'img/sales_coach_npc2.webp',
    #     'SALES COACH INBOUND': 'img/sales_coach_npc3.png',
    #     'TUTOR': 'img/tutor_npc2.png',
    # }


    return render_template('characters.html', npcs=persona_files, temp=temp, persona_gen=persona_gen)


@app.route('/char_select/<npc_name>', methods=['GET'])
def char_select(npc_name):
    # Get the persona file for the selected character
    persona = get_persona(npc_name.lower())

    # Redirect to the chat route with the persona as a parameter
    return redirect(url_for('chat', persona=persona))


@app.route('/chat/<persona>', methods=['GET'])
def chat(persona):
    # Render the chat template with the persona
    print(persona)
    message = f"Hello, how can I help you?"
    return render_template('chat.html', persona=persona, intro_message=message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    # handle form submission...
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):

            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username/password combination')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
    # handle form submission...
    return render_template('register.html', form=form)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


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


@app.route('/upload_folder', methods=['POST', 'GET'])
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
