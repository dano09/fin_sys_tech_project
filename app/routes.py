from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User
from app import app, db
from app.forms import LoginForm, RegistrationForm, HelloForm


@app.route('/')
@app.route('/index')
def index():
    print('inside /index route')
    form = HelloForm(request.form)
    return render_template('index.html', title='Home', form=form)


@app.route('/hello', methods=['POST'])
def hello():
    print('inside /hello route')

    form = HelloForm(request.form)

    print('form is: {}'.format(form))
    print('form.sayhello is: '.format(form.sayhello))
    print('form.validate is: '.format(form.validate_on_submit()))
    print('request.method is: {}'.format(request.method))
    if request.method == 'POST' and not form.validate_on_submit():
        print('got here xD')
        name = request.form['sayhello']
        print('name is: {}'.format(name))
        return render_template('hello.html', name=name)

    print('About to redirect to index')
    return render_template('index.html', form=form)


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