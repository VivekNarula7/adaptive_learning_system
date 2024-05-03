from flask import render_template, redirect, url_for, flash, request, jsonify
from adaptive_learning_system import app, db, bcrypt
from adaptive_learning_system.forms import RegistrationForm, LoginForm, UpdateAccountForm, ProgrammingQuestionForm
from adaptive_learning_system.models import User, ProgrammingQuestion, Submission, GeneratedCode
from flask_login import login_user, current_user, logout_user, login_required
import sys
from io import StringIO
import subprocess
import tempfile
import os
import requests
from transformers import pipeline
from hugchat import hugchat
from hugchat.login import Login


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
    question = None  # Initialize question variable outside the if block
    if form.validate_on_submit():
        # Start a database transaction
        with db.session.begin_nested():
            question = ProgrammingQuestion(
                title=form.title.data,
                description=form.description.data,
                difficulty=form.difficulty.data,
                language=form.language.data,
            )
            db.session.add(question)
            db.session.commit()
            flash("Question added successfully!", "success")
        return redirect(url_for("view_questions"))
    else:
        # Handle form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "danger")
    return render_template("add_question.html", title="Add Question", form=form, question=question)


@app.route("/view_questions")
def view_questions():
    questions = ProgrammingQuestion.query.all()
    return render_template("view_questions.html", questions=questions)


@app.route('/submit', methods=['POST'])
@login_required
def submit():
    user_id = current_user.id
    code = request.form['code']
    question_id = request.form['question_id']

    # Retrieve the question details
    question = ProgrammingQuestion.query.get_or_404(question_id)

    submission = Submission(user_id=user_id, question_id=question_id, code=code)

    print(submission)

    db.session.add(submission)
    db.session.commit()

    return redirect(url_for('result', submission_id=submission.id))


@app.route('/test_transformer', methods=['GET'])
def test_transformer():
    # Define the prompt
    generator = pipeline('text-generation', model='gpt2', device=-1)

    prompt = "Once upon a time in a far away land,"

    # Generate text using the pipeline
    generated_text = generator(prompt, max_length=100, num_return_sequences=1)[0]['generated_text']

    # Return the generated text as the response
    return jsonify({'generated_text': generated_text})


@app.route("/solve_question/<int:question_id>", methods=['GET', 'POST'])
@login_required
def solve_question(question_id):
    question = ProgrammingQuestion.query.get_or_404(question_id)
    if request.method == 'POST':
        user_code = request.form.get("user_code")
        if user_code:
            # Store the user's code submission in the database
            submission = Submission(user_id=current_user.id, question_id=question_id, code=user_code)
            db.session.add(submission)
            db.session.commit()
            flash('Your code has been submitted successfully!', 'success')
            return redirect(url_for('some_result_route', question_id=question_id))
        else:
            flash('No code was submitted.', 'warning')

    return render_template('solve_question.html', question=question)


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


def generate_response(prompt_input, email, passwd):
    # Hugging Face Login
    sign = Login(email, passwd)
    cookies = sign.login()
    # Create ChatBot
    chatbot = hugchat.ChatBot(cookies=cookies.get_dict())
    response_message = chatbot.chat(prompt_input)
    return response_message  # Extract text from the message object

@app.route('/evaluate', methods=['POST'])
@login_required
def evaluate():
    # Get the user's code submission and the programming question from the request
    user_code = request.form['code']
    question_id = request.form['question_id']
    question_description = ProgrammingQuestion.query.get_or_404(question_id)

    # Extract prompt text from the question description
    prompt_text = question_description.description

    # Combine prompt text with user's code
    prompt = f"Solve the following question: {prompt_text}\n\n Is the User's code:\n{user_code} correct based on the {prompt_text}. Provide detailed code analysis of the User's code:\n{user_code}"

    # Generate LLM response using Hugging Chat
    chatbot_response = generate_response(prompt, email='viveknarula22@gmail.com', passwd='Vivek*2407')

    # Here, you can analyze chatbot_response to determine if the user's code is correct or not
    # For simplicity, let's assume the chatbot_response contains feedback on the code
    # You can adjust this part based on the actual format of the response from your LLM

    # Return the generated conversational response
    return str(chatbot_response)
