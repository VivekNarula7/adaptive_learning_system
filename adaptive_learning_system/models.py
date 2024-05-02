# models.py

from datetime import datetime
from adaptive_learning_system import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class ProgrammingQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    test_case1_input = db.Column(db.String(100), nullable=False)
    test_case1_output = db.Column(db.String(100), nullable=False)
    test_case2_input = db.Column(db.String(100), nullable=False)
    test_case2_output = db.Column(db.String(100), nullable=False)
    test_case3_input = db.Column(db.String(100), nullable=False)
    test_case3_output = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"ProgrammingQuestion(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')"
