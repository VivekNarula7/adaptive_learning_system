from flask import render_template, redirect, url_for, flash, request, jsonify
from adaptive_learning_system import app, db, bcrypt
from adaptive_learning_system.forms import RegistrationForm, LoginForm, UpdateAccountForm, ProgrammingQuestionForm
from adaptive_learning_system.models import User, ProgrammingQuestion
from flask_login import login_user, current_user, logout_user, login_required
import sys
from io import StringIO
import subprocess
import tempfile
import os

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated", "success")
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.route("/add_question", methods=["GET", "POST"])
@login_required
def add_question():
    form = ProgrammingQuestionForm()
    if form.validate_on_submit():
        question = ProgrammingQuestion(
            title=form.title.data,
            description=form.description.data,
            difficulty=form.difficulty.data,
            language=form.language.data,
            user_id=current_user.id,
            test_case1_input=form.test_case1_input.data,
            test_case1_output=form.test_case1_output.data,
            test_case2_input=form.test_case2_input.data,
            test_case2_output=form.test_case2_output.data,
            test_case3_input=form.test_case3_input.data,
            test_case3_output=form.test_case3_output.data
        )
        db.session.add(question)
        db.session.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for("view_questions"))
    return render_template("add_question.html", title="Add Question", form=form)

@app.route("/view_questions")
def view_questions():
    questions = ProgrammingQuestion.query.all()
    return render_template("view_questions.html", questions=questions)

@app.route('/compile', methods=['POST'])
def compile_code():
    code = request.form['code']
    try:
        # Secure execution using a temporary file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            f.write(code)
            f.flush()
            output = subprocess.run(
                ['python', f.name], capture_output=True, text=True, timeout=5)
        os.remove(f.name)  # Ensure the file is removed after execution
        if output.returncode == 0:
            return output.stdout
        else:
            return f"Error in execution: {output.stderr}"
    except Exception as e:
        return f"Server error: {str(e)}", 500

@app.route('/run_test_cases', methods=['POST'])
def run_test_cases():
    data = request.get_json()
    code = data['code']
    test_cases = data['test_cases']
    results = []
    try:
        for test in test_cases:
            output = execute_user_code(code, test['input'])
            results.append({
                'input': test['input'],
                'expected_output': test['expected_output'],
                'actual_output': output,
                'pass': output.strip() == test['expected_output'].strip()
            })
        return jsonify(results=results)
    except Exception as e:
        app.logger.error(f"Failed to execute test cases: {str(e)}")
        return jsonify(error=str(e)), 500

def execute_user_code(code, input_data):
    """
    Execute user submitted code securely and capture the output.
    """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write(code)
        f.flush()
        result = subprocess.run(
            ['python', f.name],
            input=input_data, capture_output=True, text=True, timeout=5)
    os.remove(f.name)
    if result.returncode == 0:
        return result.stdout
    else:
        return f"Execution error: {result.stderr}"

@app.route("/solve_question/<int:question_id>", methods=['GET', 'POST'])
@login_required
def solve_question(question_id):
    question = ProgrammingQuestion.query.get_or_404(question_id)
    
    # Fetching test cases as a list of dictionaries
    test_cases = [
        {'input': question.test_case1_input, 'output': question.test_case1_output},
        {'input': question.test_case2_input, 'output': question.test_case2_output},
        {'input': question.test_case3_input, 'output': question.test_case3_output}
    ]

    if request.method == 'POST':
        user_code = request.form.get("user_code")
        # Further processing can be done here
        return redirect(url_for("some_result_route", question_id=question_id))
    
    return render_template('solve_question.html', question=question, test_cases=test_cases)
