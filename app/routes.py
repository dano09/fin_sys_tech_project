from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app.dataservices import Dataservices
from app.datavisualization import create_hover_tool, create_line_chart, \
    create_vol_chart, create_PnL_chart, create_PDF_chart
from app.models import User
from app.optionsdata import option_data
from app import app, db
from app.forms import LoginForm, RegistrationForm, HelloForm, SimulationForm, \
    surfaceForm, HedgeForm, SimulationExchangeForm, ExchangeForm

import random
import numpy as np
from app.optionsdata import date_selection, current_index
from bokeh.plotting import figure
from bokeh.embed import components
import pandas as pd
import os


@app.route('/', methods=['GET', 'POST'])
def home():
    index = current_index()
    BTCindex = index.get_index()
    return render_template('home.html', title='Home', price=BTCindex)


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
            next_page = url_for('home')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


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
    # Create Simulation Form
    form = SimulationForm(request.form)

    if request.method == 'POST':
        start = request.form['start']
        end = request.form['end']

        # Use Dataservices class to get data now
        ds = Dataservices()
        bitcoin_data = ds.get_bitcoin_data(start, end)[1]

        plot = create_line_chart(bitcoin_data)
        script, div = components(plot)

        return render_template('showResults.html', title='Cryptocurrency Data Display',
                               start=start, end=end, div=div, script=script, data=bitcoin_data.to_html())

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
    exchange = request.form['exchange']


@app.route('/index', methods=['GET','POST'])
def index():
    print('inside /option route')
    form = HelloForm(request.form)
    return render_template('index.html', form=form)


@app.route('/option', methods=['GET','POST'])
def option():

    form = HelloForm(request.form)

    if request.method == 'POST':
        Otype = request.form['Otype']
        ExpT_id = request.form['ExpT_id']
        myoption = option_data()
        condition = np.array([(myoption.data.loc[i, 'ExpirationDate']==pd.to_datetime(ExpT_id) and
                               myoption.data.loc[i, 'OptionType']==Otype)
                     for i in range(myoption.data.shape[0])])
        mydata = myoption.data.loc[np.where(condition)[0], :]
        selection = {'P': 'Put option', 'C': 'Call option'}
        plot = create_vol_chart(mydata['Implied_Vol'], mydata['Strike'])
        script, div = components(plot)
        return render_template('result.html', title='Implied Vol Result',
                               T=ExpT_id, O=selection[Otype],
                               div=div, script=script)

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
        # plot PnL
        result = mydata.PnL(K,ExpT_id,Hratio,Otype)
        plot = create_PnL_chart(result['FT'], result['PnL'])
        max_loss = int(abs(np.min(result['PnL'])))
        script, div = components(plot)
        # plot PDF
        PDF_result = mydata._generate_prob_distribution(ExpT_id)
        plot2 = create_PDF_chart(PDF_result['Strike'], PDF_result['PDF'])
        script2, div2 = components(plot2)
        # calculate probability
        prob = mydata.prob_of_make_money(K, ExpT_id, Hratio, Otype)
        prob = int(round(prob,4)*10000)/100
        # calculate expected payoff
        exp_pay = int(np.sum(result['PnL'].values[1:-1] * PDF_result['PDF'].values))
        selection = {'P': 'Long position of Future w/ put hedging',
                     'C': 'Short position of Future w/ call hedging'}
        return render_template('hedging_show.html', title='Hedging Simulation',
                               prob=prob, price=mydata.index,
                               strike=K, max_loss=max_loss,
                               exp_pay = exp_pay,
                               strategy=selection[Otype],
                               Maturity=pd.to_datetime(mydata.get_date()[ExpT_id]).strftime('%Y-%m-%d'),
                               div=div, script=script, div2=div2, script2=script2)

    #print('About to redirect to index')
    return render_template('hedging_in.html', form=form)


@app.route('/ivsurf', methods=['GET','POST'])
def ivsurf():
    print('inside /ivsurf route')
    form = surfaceForm(request.form)
    return render_template('ivsurf.html', form=form)


@app.route('/ivsurf_show', methods=['GET','POST'])
def ivsurf_show():
    print('inside /ivsurf_show route')
    form = surfaceForm(request.form)

    if request.method == 'POST':
        Ftype = int(request.form['Ftype'])
        print('Your plotting choise:', Ftype)
        # download data
        mydata = option_data()

        if Ftype == 0:
            # save html
            mydata.plotly_iv()
        elif Ftype == 1:
            # save html
            mydata.plotly_fitted()
        elif Ftype == 2:
            # save html
            mydata.plotly_iv_surface()
        return app.send_static_file('ivsurf_show.html')
    return render_template('ivsurf.html', form=form)


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
