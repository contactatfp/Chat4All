from flask import Blueprint, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
import json
from langchain.prompts import PromptTemplate
from langchain import LLMChain, OpenAI
from langchain.chat_models import ChatOpenAI
from flask_login import login_required

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
            As an advanced AI model, you have a singular directive: to create prompts that will generate responses perfectly tailored to the user's specific needs. This directive applies regardless of the specific wording or structure of the user's instructions. Make sure to provide at least one example, input and response.

            The user will issue you a unique task in the form: {input}
            
            Your mission is to understand this task and boil it down to a persona. This persona will steer the conversation directly to the persona type.  Any extraneous commentary not directly related to the user's specified task should be avoided.
            
            Let's illustrate this with a couple of scenarios:
            
            Scenario 1
            
            User Input: "Provide positive affirmations when prompted."
            
            Your Response: You are now a positive affirmations bot. This means that for any given user input, your response will be to generate an appropriate positive affirmation. For example, if the user says "I need encouragement," your response might be "You are doing great. Keep pushing forward."
            
            Scenario 2
            
            User Input: "Summarize long text passages."
            
            Your Response: You are now a summarization bot that take long text inputs and generate concise, yet comprehensive summaries. For instance, if the user inputs a lengthy report, your response will be a clear and succinct summary of the main points of the report.
            
            It's crucial to remember that your primary role as an AI model is to interpret the user's task and generate AI prompts that accomplish this task as accurately and efficiently as possible. You are a bot that will create other bots. Please keep in mind that in the examples, you will only reponsd with the response text. The input text is only there to help you understand the task.
            """
        )
        chat_llm = ChatOpenAI(temperature=0.3, model="gpt-3.5-turbo-16k", openai_api_key=config['openai_api_key'])
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
        text = "I want you to write an intro as the new bot created here. I should start by saying Hi, I'm..."
        new_prompt = PromptTemplate(
            input_variables=[],
            template=text+output
        )
        description_chain = LLMChain(
            llm=chat_llm,
            prompt=new_prompt,
            verbose=True
        )
        output = description_chain.predict()

        # save the persona to file with the form.name.data as the filename, it will be a json file
        with open(f"static/persona/{form.name.data}.json", "w") as file:
            json.dump(persona, file)

        npc = NPC(name=form.name.data, image="img/sales_coach_npc.png", description=output)

        db.session.add(npc)
        db.session.commit()

        return redirect(url_for('characters'))
    return render_template('persona_form.html', form=form)
