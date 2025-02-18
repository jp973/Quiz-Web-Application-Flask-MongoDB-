from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import re
import datetime

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/quizz'
app.config['SECRET_KEY'] = 'your_secret_key_here'

mongo = PyMongo(app)

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = mongo.db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['email'] = user.get('email', '')
            session['age'] = user.get('age', '')
            session['address'] = user.get('address', '')
            session['phone'] = user.get('phone', '')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone = request.form['phone']

        # Check if username or email already exists
        existing_user = mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            flash('Username or Email already exists')
            return redirect(url_for('register'))

        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))

        # Validate phone number
        if not re.match(r'^[0-9]{10}$', phone):
            flash('Invalid phone number format')
            return redirect(url_for('register'))

        # If all validations pass, hash the password and insert into MongoDB
        hashed_password = generate_password_hash(password)
        new_user = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'age': int(age),
            'gender': gender,
            'address': address,
            'phone': phone
        }

        mongo.db.users.insert_one(new_user)
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        user = mongo.db.users.find_one({'username': username})
        if user:
            return render_template('profile.html', user=user)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session['username'])

@app.route('/gk')
def gk_quiz():
    return render_template('gk.html')

@app.route('/quiz1')
def quiz1():
    return render_template('quiz1.html')

@app.route('/science')
def science_quiz():
    return render_template('science.html')

@app.route('/quiz2')
def quiz2():
    return render_template('quiz2.html')

@app.route('/history')
def history_quiz():
    return render_template('history.html')

@app.route('/quiz3')
def quiz3():
    return render_template('quiz3.html')

# Define correct answers for quizzes
correct_answers_gk = {
    "q1": "b",  # Paris
    "q2": "c",  # William Shakespeare
    "q3": "b",  # Mercury
    "q4": "b",  # 1912
    "q5": "b",  # Leonardo da Vinci
    "q6": "b",  # Yen
    "q7": "c",  # Alexander Fleming
    "q8": "a",  # Nile
    "q9": "c",  # Diamond
    "q10": "a"  # Charles Babbage
}

correct_answers_science = {
    "q1": "b",  # H2O
    "q2": "c",  # Albert Einstein
    "q3": "b",  # Mars
    "q4": "b",  # 300,000 km/s
    "q5": "c",  # Albert Einstein
    "q6": "b",  # Mitochondria
    "q7": "b",  # JavaScript
    "q8": "c",  # Skin
    "q9": "b",  # Nitrogen
    "q10": "a"  # Central Processing Unit
}

correct_answers_history = {
    "q1": "b",  # Example answer
    "q2": "c",  # Example answer
    "q3": "a",  # Example answer
    "q4": "d",  # Example answer
    "q5": "b",  # Example answer
    "q6": "a",  # Example answer
    "q7": "c",  # Example answer
    "q8": "b",  # Example answer
    "q9": "d",  # Example answer
    "q10": "a"  # Example answer
}

@app.route('/submit1', methods=['POST'])
def submit1():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    # Retrieve the quiz type and correct answers based on quiz type
    quiz_type = request.form.get('quiz_type')
    if quiz_type == "gk":
        correct_answers = correct_answers_gk
    elif quiz_type == "science":
        correct_answers = correct_answers_science
    elif quiz_type == "history":
        correct_answers = correct_answers_history
    else:
        flash('Invalid quiz type')
        return redirect(url_for('dashboard'))

    # Retrieve user answers from the form
    user_answers = {f"q{i+1}": request.form.get(f"q{i+1}") for i in range(10)}

    # Calculate the user's score
    score = sum(1 for q, ans in user_answers.items() if ans == correct_answers[q])

    # Store the result details
    results = {f'q{i+1}': {
        'correct': correct_answers[f'q{i+1}'],
        'user': user_answers.get(f'q{i+1}', 'None'),
        'is_correct': (user_answers.get(f'q{i+1}', 'None') == correct_answers[f'q{i+1}'])
    } for i in range(10)}

    # Save the quiz results to MongoDB
    quiz_result = {
        'username': session['username'],
        'quiz_type': quiz_type,
        'user_answers': user_answers,
        'correct_answers': correct_answers,
        'score': score,
        'submission_time': datetime.datetime.now()
    }

    mongo.db.user_answers.insert_one(quiz_result)

    # Return the results page to the user
    return render_template('submit1.html', score=score, results=results)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/retry')
def retry():
    quiz_type = session.get('quiz_type')
    if quiz_type:
        return redirect(url_for(quiz_type))
    else:
        flash('No quiz type found, redirecting to home.')
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
