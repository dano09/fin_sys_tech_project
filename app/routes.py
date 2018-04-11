from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app.datavisualization import create_hover_tool, create_bar_chart
from app.models import User
from app.optionsdata import option_data
from app import app, db
from app.forms import LoginForm, RegistrationForm, HelloForm, SimulationForm, OptionForm

import random
from bokeh.embed import components
from flask import Flask, render_template
import pandas as pd
import os

@app.route('/')
@app.route('/index')
def index():
    print('inside /index route')
    form = HelloForm(request.form)
    return render_template('index.html', title='Home', form=form)


@app.route('/hello', methods=['POST'])
def hello():
    print('inside /hello route')

    # Re-creates the HelloForm Object
    form = HelloForm(request.form)

    if request.method == 'POST' and not form.validate_on_submit():
        # This will simply get the name provided by the user from html
        name = request.form['sayhello']
        print('name is: {}'.format(name))

        # This will re-create the wtforms.fields.core.StringField object
        # not used here but could be useful
        name2 = form['sayhello']
        print('name2 is: {}'.format(type(name2)))

        # This will re-create the wtforms.fields.core.SubmitField object
        # not used here but could be useful
        submit = form['submit']
        print('submit is: {}'.format(type(submit)))

        return render_template('hello.html', name=name)

    print('About to redirect to index')
    return render_template('index.html', form=form)


@app.route('/chart', methods=['GET', 'POST'])
def chart():
    form = HelloForm(request.form)  

    if request.method == 'POST':
        bars_count = int(request.form['barc'])
        print('bars_count is: {}'.format(bars_count))
        if bars_count <= 0:
            bars_count = 1

    data = {"days": [], "bugs": [], "costs": []}
    for i in range(1, bars_count + 1):
        data['days'].append(str(i))
        data['bugs'].append(random.randint(1, 100))
        data['costs'].append(random.uniform(1.00, 1000.00))

    hover = create_hover_tool()
    plot = create_bar_chart(data, "Bugs found per day", "days", "bugs", hover)
    script, div = components(plot)

    return render_template("chart.html", bars_count=bars_count, the_div=div, the_script=script, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/start_simulation')
def start_simulation():
    print('inside /start_simulation route')
    form = SimulationForm(request.form)
    return render_template('simulation.html', title='Simulation', form=form)


@app.route('/simulation', methods=['GET', 'POST'])
def simulation():
    print('inside /simulation route')

    # Create Simulation Form
    form = SimulationForm(request.form)

    if request.method == 'POST':
        print('got here xD')
        start = request.form['start']
        end = request.form['end']

        print('startdate is: {} and type is {}'.format(start, type(start)))
        print('enddate is: {}'.format(end))

        # Path will be different when running on your local
        bitcoin_data = pd.read_csv('C:/Users/liuyu/source/repos/fin_sys_tech_project/data/coindesk_bitcoin.csv')

        print('bitcoin_data is {}'.format(bitcoin_data.tail()))
        print('bitcoin_data is {}'.format(type(bitcoin_data)))

        data = bitcoin_data[(bitcoin_data['Date'] >= start) & (bitcoin_data['Date'] <= end)]
        print('data is : {}'.format(data))
        return render_template('showResults.html', start=start, end=end, data=data.to_html())

    print('About to redirect to index')
    return render_template('index.html', form=form)


@app.route('/option', methods=['GET','POST'])
def option():
    print('inside /option route')

    form = HelloForm(request.form)

    if request.method == 'POST':
        print('got here xD')
        OPrice = request.form['OPrice']
        ExpT = request.form['ExpT']
        S = request.form['S']
        K = request.form['K']
        rate = request.form['rate']
        Otype = request.form['Otype']

        volresult = pd.DataFrame((option_data(rate).data['Implied_Vol']).astype(int))

        print('vol result is: {}'.format(volresult))

        #print('data is : {}'.format(name))

        return render_template('result.html', Price=OPrice, T=ExpT, S=S, K=K, 
                               i=rate, O=Otype, form=form)

    #print('About to redirect to index')
    #return render_template('index.html', form=form)

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)