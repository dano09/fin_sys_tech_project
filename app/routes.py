from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app.dataservices import Dataservices
from app.datavisualization import create_hover_tool, create_bar_chart, create_line_chart, create_vol_chart, create_PnL_chart
from app.models import User
from app.optionsdata import option_data
from app import app, db
from app.forms import LoginForm, RegistrationForm, HelloForm, SimulationForm, \
    OptionForm, surfaceForm, HedgeForm, SimulationExchangeForm, ExchangeForm

import random
from app.optionsdata import date_selection, current_index
import matplotlib.pyplot as plt, mpld3
from bokeh.plotting import figure
from bokeh.embed import components
import pandas as pd
import os


@app.route('/')
def home():
    print('inside / route')
    index = current_index()
    BTCindex = index.get_index()
    return render_template('base.html', title='Home', price=BTCindex)

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

    return render_template("chart.html", title='Bar charts with Bokeh', bars_count=bars_count, the_div=div, the_script=script, form=form)


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
        start = request.form['start']
        end = request.form['end']

        print('startdate is: {} and type is {}'.format(start, type(start)))
        print('enddate is: {}'.format(end))

        # Use Dataservices class to get data now
        ds = Dataservices()
        bitcoin_data = ds.get_bitcoin_data(start, end)[1]

        plot = create_line_chart(bitcoin_data)
        script, div = components(plot)

        return render_template('showResults.html', title='Cryptocurrency Data Display',
                               start=start, end=end, div=div, script=script, data=bitcoin_data.to_html())

    print('About to redirect to index')
    return render_template('index.html', form=form)


@app.route('/exchangeForm')
def exchangeForm():
    form = ExchangeForm()
    return render_template('showExchanges.html', form=form)


@app.route('/processExchange', methods=['POST'])
def process():
    exchange = request.form['exchange']
    if exchange:
        return jsonify({'exchange': exchange})
    return jsonify({'error': 'missing data..'})


@app.route('/exchanges')
def exchangedic():
    ds = Dataservices()
    exchange_choices = ds.get_exchanges()
    exchange_list = [{'name': ex} for ex in exchange_choices]
    return jsonify(exchange_list)


@app.route('/get_symbol_id_for_exchange', methods=['POST'])
def get_symbol_ids():
    print('-----inside ajax get_symbol_ids--------')
    exchange = request.form['exchange']
    print('exchange is : {}'.format(exchange))

    #return jsonify({'text': translate(request.form['text'],
    #                                  request.form['source_language'],
    #                                  request.form['dest_language'])})

@app.route('/index', methods=['GET','POST'])
def index():
    print('inside /option route')
    form = HelloForm(request.form)
    return render_template('index.html', form=form)

@app.route('/option', methods=['GET','POST'])
def option():
    print('inside /option route')

    form = HelloForm(request.form)

    if request.method == 'POST':
        Otype = request.form['Otype']
        ExpT_id = request.form['ExpT_id']
        myoption = option_data()
        mydata = myoption.data.loc[myoption.data['ExpirationDate']==ExpT_id, :]
        plot = create_vol_chart(mydata['Implied_Vol'], mydata['Strike'])
        script, div = components(plot)
        return render_template('result.html', title='Implied Vol Result',
                               T=ExpT_id, O=Otype, div=div, script=script)

    #print('About to redirect to index')
    return render_template('index.html', form=form)

@app.route('/hedging', methods=['GET','POST'])
def hedging():
    print('inside /hedging route')
    form = HedgeForm(request.form)
    return render_template('hedge_in.html', form=form)

@app.route('/hedging_sim', methods=['GET','POST'])
def hedging_sim():
    print('inside /hedging_sim route')

    form = HedgeForm(request.form)

    if request.method == 'POST':
        Hratio = float(request.form['Hratio'])
        K = int(request.form['K'])
        ExpT_id = int(request.form['ExpT_id'])
        Otype = request.form['Otype']
        mydata = option_data()
        result = mydata.PnL(K,ExpT_id,Hratio,Otype)
        plot = create_PnL_chart(result['FT'], result['PnL'])
        script, div = components(plot)

        #probability
        prob = mydata.prob_of_make_money(ExpT_id,K,Otype)
        return render_template('hedging_show.html', title='Hedging Simulation',
                               prob=prob*100, price=mydata.index,
                               div=div, script=script)

    #print('About to redirect to index')
    return render_template('hedging_in.html', form=form)

@app.route('/ivsurf', methods=['GET','POST'])
def ivsurf():
    print('inside /ivsurf route')
    form = surfaceForm(request.form)
    return render_template('ivsurf.html', form=form)


@app.route('/ivsurf_show', methods=['GET, POST'])
def iv_surface_show():
    pass


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
