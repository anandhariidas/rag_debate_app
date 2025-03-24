from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import ollama
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirect root URL to login page

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            # flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        topic = request.form.get('topic')
        if not topic:
            flash("Please enter a topic!", "error")
            return redirect(url_for('dashboard'))
        
        response = debate_assistant(topic)
        return render_template('index.html', topic=topic, response=response)

    return render_template('index.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

def fetch_web_info(topic):
    """Fetches information from the RAG system."""
    try:
        response = requests.post(
            "http://localhost:5000/rag",
            json={"text_query": topic},
            headers={"Content-Type": "application/json"},
            timeout=8
        )
        
        if response.status_code == 200:
            return response.json().get("content", ""), response.json().get("sources", [])
        
    except Exception as e:
        print(f"Web search error: {str(e)}")
    
    return "", []

def debate_assistant(topic):
    """Generates arguments, counterarguments, and a summary for a debate topic."""
    print(f"Generating debate on: {topic}")
    
    # Fetch web information
    print("Searching for information...")
    web_info, sources = fetch_web_info(topic)
    
    if web_info:
        print(f"Found information from {len(sources)} sources")
    else:
        print("No web information found. Proceeding with base knowledge only.")
    
    # System message
    system_message = (
        "You are a debate assistant AI. Generate a structured response for the given topic. "
        "Ensure the response is logical, evidence-based, and includes:"
        "1. Arguments supporting the topic\n"
        "2. Counterarguments\n"
        "3. A concise summary"
    )
    
    # User message
    user_message = f"Topic: {topic}\n\n"
    if web_info:
        user_message += f"Relevant information:\n{web_info}\n\n"
    
    user_message += "Generate:\n1. Arguments in favor\n2. Arguments against\n3. Summary"
    
    # Call Ollama model
    print("Generating response...")
    try:
        response = ollama.chat(
            model='llama3.2:1b',
            messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': user_message}
            ]
        )
        
        return response['message']['content']
    except Exception as e:
        return f"Error generating debate: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure this runs within the app context
    app.run(debug=True)
