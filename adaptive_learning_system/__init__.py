from flask import Flask, Blueprint, send_from_directory, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
from wtforms.validators import ValidationError
import requests

current_dir = os.path.abspath(os.path.dirname(__file__))

# Create the Flask application instance
app = Flask(__name__)

# Set the OpenAI API import os
# Configure Flask settings
app.config['SECRET_KEY'] = '1da104351ce04785a9a58c6e81021b73b41046579f685f47a3915ac32ec6c9c9'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(current_dir, "database.db")

# Initialize Flask extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# Configure login manager settings
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Initialize login manager with the app
login_manager.init_app(app)

# Push the app context to make it accessible in blueprints
app.app_context().push()

# Import routes and models
from adaptive_learning_system import routes, models