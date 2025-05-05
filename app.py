import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Route for home page
@app.route('/')
def index():
    # Some basic information to display
    info = {
        "title": "وب‌سایت ساده با فلسک",
        "description": "این یک وب‌سایت ساده با استفاده از فلسک است.",
        "features": [
            "ساخته شده با فلسک",
            "طراحی ساده و زیبا",
            "فرم ساده برای ارسال اطلاعات"
        ]
    }
    return render_template('index.html', info=info)

# Route for form submission
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        message = request.form.get('message', '')
        
        # Check if form data is valid
        if name and email and message:
            # In a real app, you might save this to a database
            # For now, just display the submitted information
            submission = {
                'name': name,
                'email': email,
                'message': message
            }
            return render_template('success.html', submission=submission)
        else:
            flash('لطفاً تمام فیلدها را پر کنید.', 'danger')
            return redirect(url_for('index'))
