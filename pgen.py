from flask import Blueprint, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
import json
from langchain.prompts import PromptTemplate
from langchain import LLMChain, OpenAI
from langchain.chat_models import ChatOpenAI

from models import db

with open('config.json') as f:
    config = json.load(f)

pgen = Blueprint('pgen', __name__)


class PersonaForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    # input_variables = StringField('input_variables')
    template = TextAreaField('template', validators=[DataRequired()])
    submit = SubmitField('Generate Persona')


@pgen.route('/persona_form', methods=['GET', 'POST'])
def persona_form():
    from models import NPC
    from flask_login import current_user
    from app import ask_your_model
    # if request is a post then generate the persona
    form = PersonaForm()
    if form.validate_on_submit():
        # create a db npc object with the form.name.data
        prompt = PromptTemplate(
            input_variables=['input'],
            template="""
            You are an AI model, a digital assistant tasked with crafting specialized responses based on the instructions provided by the user. Your objective is to interpret and translate user instructions into actions, producing tailored responses that align perfectly with the user's specified needs.

The user has presented you with the following directive: {input}

Your role, as an AI model, is to act according to this directive, delivering responses that strictly adhere to the guidelines outlined in the user's input. It's crucial to note that your responses should be limited to the requested action without deviating into unrelated or unsolicited commentary.

For example, consider the following scenarios:

Scenario 1

Input: The user asks you to "Create an AI assistant that gives positive affirmations when prompted."

Response: Your task is to develop AI prompts that consistently produce positive affirmations. As such, whenever prompted, you will analyze the input and craft suitable positive affirmations that align with the context and tone of the input.

You might provide an affirmation like, "You are capable and strong. You can overcome any obstacles that stand in your way." The nature of the affirmation may vary depending on the context of the user's prompt.

Scenario 2

Input: The user instructs you to "Create an AI assistant to summarize long text passages."

Response: In this case, your role is to process lengthy text passages provided by the user and generate concise, informative summaries. For example, the user might input a complex academic paper or a lengthy news article, and your task is to distill the key points into a brief summary that retains the essence of the original text.

Remember, each user input is unique, and your responses should be tailored to address the specific request detailed in each instruction. As an AI model, your role is to interpret and execute these instructions with precision, aiding the user in their desired task.
            """
        )
        chat_llm = ChatOpenAI(model="gpt-3.5-turbo-16k", openai_api_key=config['openai_api_key'])
        chatgpt_chain = LLMChain(
            llm=chat_llm,
            prompt=prompt,
            verbose=True
        )

        output = chatgpt_chain.predict(input=form.template.data)

        persona = {
            "_type": "prompt",
            "input_variables": ["input"],
            "template": output
        }
        new_prompt = PromptTemplate(
            input_variables=[],
            template=output
        )
        description_chain = LLMChain(
            llm=chat_llm,
            prompt=new_prompt,
            verbose=True
        )
        output = description_chain.predict(input="Write an intro paragraph from the new bots perspective.")

        # save the persona to file with the form.name.data as the filename, it will be a json file
        with open(f"static/persona/{form.name.data}.json", "w") as file:
            json.dump(persona, file)

        npc = NPC(name=form.name.data, image="img/sales_coach_npc.png", description=output, user_id=current_user.id)

        db.session.add(npc)
        db.session.commit()

        return redirect(url_for('characters'))
    return render_template('persona_form.html', form=form)
