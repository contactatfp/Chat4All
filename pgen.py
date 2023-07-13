from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
import json

pgen = Blueprint('pgen', __name__)

class PersonaForm(FlaskForm):
    input_variables = StringField('input_variables')
    template = TextAreaField('template', validators=[DataRequired()])
    submit = SubmitField('Generate Persona')

@pgen.route('/persona_form', methods=['GET', 'POST'])
def persona_form():
    # if request is a post then generate the persona
    form = PersonaForm()
    if form.validate_on_submit():
        persona = {
            "_type": "prompt",
            "input_variables": [form.input_variables.data],
            "template": form.template.data
        }
        with open('sales_coach_outbound.json', 'w') as f:
            json.dump(persona, f, indent=4)
        return 'Persona generated!'
    return render_template('persona_form.html', form=form)
