from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, RadioField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length

from app import dataservices
from app.optionsdata import date_selection, current_index
from app.dataservices import Dataservices
from app.models import User
from wtforms.fields.html5 import DateField
from wtforms.fields import SelectField


class HelloForm(FlaskForm):
    Otype = SelectField('Option Type', choices=[('Put option', 'Put option'),('Call option', 'Call option')],
                        description='Select the option type you go long with.')
    dates_obj = date_selection()
    dates = dates_obj.get_date()
    ExpT_id = SelectField('Maturity', choices=[(dates[0], dates[0].strftime('%Y-%m-%d')),
                                            (dates[1], dates[1].strftime('%Y-%m-%d')),
                                            (dates[2], dates[2].strftime('%Y-%m-%d'))])
    submit = SubmitField('Plot Implied Volatility')
    

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
    start = DateField('startDate', format='%Y-%m-%d')
    end = DateField('endDate', format='%Y-%m-%d')
    submit = SubmitField('Show Data')


# For testing AJAX
class ExchangeForm(FlaskForm):
    exchange = StringField('Exchange', validators=[DataRequired(), Length(max=40)], render_kw={"placeholder": "exchange"})


class SimulationExchangeForm(FlaskForm):
    ds = Dataservices()
    exchange_choices = ds.get_exchanges()
    exchange_list = [(ex, ex) for ex in exchange_choices]
    exchanges = SelectField(label='Exchanges', choices=exchange_list)
    submit = SubmitField('Pick an Exchange')

class surfaceForm(FlaskForm):
    Ftype = SelectField('Figure Style:', choices=[(0, 'Scatter'),
                                                (1, 'Fitted lines'),
                                                (2, 'Full Surface')])
    submit = SubmitField('Generate Plot')

class OptionForm(FlaskForm):
    Otype = SelectField('Option Type', choices=[('Put option', 'Put option'), ('Call option', 'Call option')],
                        description='Select the option type you go long with.')
    dates_obj = date_selection()
    dates = dates_obj.get_date()
    ExpT_id = SelectField('Maturity', choices=[(dates[0], dates[0].strftime('%Y-%m-%d')),
                                            (dates[1], dates[1].strftime('%Y-%m-%d')),
                                            (dates[2], dates[2].strftime('%Y-%m-%d'))])
    submit = SubmitField('Show me IVol')


class HedgeForm(FlaskForm):
    Otype = SelectField('Option Type', choices=[('P', 'Long position of Future w/ put hedging'),
                                                ('C', 'Short position of Future w/ call hedging')],
                        description='Select the option type you go long with.')
    Hratio = StringField('Hedge Ratio', validators=[DataRequired()])
    K = StringField('Strike', validators=[DataRequired()])
    dates_obj = date_selection()
    dates = dates_obj.get_date()
    ExpT_id = SelectField('Maturity', choices=[(0, dates[0].strftime('%Y-%m-%d')),
                                            (1, dates[1].strftime('%Y-%m-%d')),
                                            (2, dates[2].strftime('%Y-%m-%d'))])

    submit = SubmitField('Simulate')
