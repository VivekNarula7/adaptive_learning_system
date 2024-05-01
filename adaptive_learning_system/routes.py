from flask import render_template, redirect, url_for, flash, request
from adaptive_learning_system import app, db, bcrypt
from adaptive_learning_system.forms import RegistrationForm, LoginForm, UpdateAccountForm, ProgrammingQuestionForm
from adaptive_learning_system.models import User, ProgrammingQuestion
from flask_login import login_user, current_user, logout_user, login_required
import sys
from io import StringIO

@app.route("/")
@app.route("/home")
def home():
    # posts = Post.query.all()
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
    image_file = url_for(
        'static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@app.route("/add_question", methods=["GET", "POST"])
@login_required
def add_question():
    form = ProgrammingQuestionForm()
    if form.validate_on_submit():
        question = ProgrammingQuestion(
            title=form.title.data,
            description=form.description.data,
            difficulty=form.difficulty.data,
            test_cases=form.test_cases.data,
            language=form.language.data,
            user_id=current_user.id
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

@app.route("/run_code", methods=["POST"])
def run_code():
    try:
        code = request.json['code']
        # Execute the code and get the output
        output = execute_code(code)
        return jsonify(output=output)
    except Exception as e:
        error_message = f"Error executing code: {str(e)}"
        app.logger.error(error_message)  # Log the exception
        return jsonify(error=error_message), 500


@app.route("/solve_question/<int:question_id>", methods=["GET", "POST"])
def solve_question(question_id):
    # Fetch the programming question from the database
    question = ProgrammingQuestion.query.get_or_404(question_id)

    if request.method == "POST":
        # Handle form submission if needed
        pass

    # Render the solve question page with the flaskcode editor
    return render_template("solve_question.html", question=question)


@app.route("/submit_solution/<int:question_id>", methods=["POST"])
def submit_solution(question_id):
    user_code = request.form.get("user_code")
    # Process the user's code here
    # You can evaluate the code, run tests, etc.
    return redirect(url_for("solve_question", question_id=question_id))

@app.route('/compile', methods=['POST'])
def compile_code():
    try:
        code = request.form['code']
        
        # Redirect stdout to capture output
        sys.stdout = StringIO()

        # Execute the code
        exec(code)

        # Get the captured output
        output = sys.stdout.getvalue()

        # Reset stdout
        sys.stdout = sys.__stdout__

        return output
    except Exception as e:
        return f'Error executing code: {str(e)}', 500