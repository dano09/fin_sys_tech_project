from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate, Config
from flask_sqlalchemy import SQLAlchemy

from app import app, db
from app.models import User

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

