from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, RadioField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo

from app import dataservices
from app.dataservices import Dataservices
from app.models import User
from wtforms.fields.html5 import DateField
from wtforms.fields import SelectField


class HelloForm(FlaskForm):
    sayhello = StringField('Greeting: ', validators=[DataRequired()])
    submit = SubmitField('Say Hello')
    barc = IntegerField('Count:', validators=[DataRequired()])
    showme = SubmitField('Plot')
    OPrice = StringField('Option Price', validators=[DataRequired()])
    ExpT = SelectField('Maturity', choices=[('One Week', '1W'),('One Month', '1M'),('Three Month', '3M')])
    S = StringField('Current Stock Price', validators=[DataRequired()])
    K = StringField('Strike Price', validators=[DataRequired()])
    rate = StringField('Interest Rate', validators=[DataRequired()])
    Otype = SelectField('Option Type', choices=[('Call Option', 'Buy'),('Put Option', 'Sell')])
    iVol = SubmitField('Show me IVol')
    

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

        def validate_email(self, email):
            user = User.query.fitler_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')


class SimulationForm(FlaskForm):
    ds = Dataservices()
    exchange_choices = ds.get_exchanges()

    exchange_list = [(ex, ex) for ex in exchange_choices]
    print('exchange_list is: {}'.format(exchange_list))

    exchanges = SelectField(label='Exchanges', choices=exchange_list)
    start = DateField('startDate', format='%Y-%m-%d')
    end = DateField('endDate', format='%Y-%m-%d')
    submit = SubmitField('Show Data')

# For testing AJAX
class OurForm(FlaskForm):
    foo = StringField('foo')

class SimulationExchangeForm(FlaskForm):
    ds = Dataservices()
    exchange_choices = ds.get_exchanges()
    exchange_list = [(ex, ex) for ex in exchange_choices]
    exchanges = SelectField(label='Exchanges', choices=exchange_list)
    submit = SubmitField('Pick an Exchange')


class OptionForm(FlaskForm):
    OPrice = StringField('Option Price', validators=[DataRequired()])
    ExpT = SelectField('Maturity', choices=[('One Week', '1W'),('One Month', '1M'),('Three Month', '3M')])
    S = StringField('Current Stock Price', validators=[DataRequired()])
    K = StringField('Strike Price', validators=[DataRequired()])
    rate = StringField('Interest Rate', validators=[DataRequired()])
    Otype = SelectField('Option Type', choices=[('Call Option', 'Buy'),('Put Option', 'Sell')])
    submit = SubmitField('Show me IVol')

