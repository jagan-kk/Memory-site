from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import mongo
from app.models import User

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # --- THIS IS THE FIX ---
    # If the user is already logged in, redirect them away from the login page.
    if current_user.is_authenticated:
        return redirect(url_for('admin.generator'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find the user in the 'users' collection of our database
        user_data = mongo.db.users.find_one({'username': username})

        # Check if user exists and password is correct
        if user_data:
            user = User(user_data) # Create a User object
            if user.check_password(password):
                login_user(user)
                return redirect(url_for('admin.generator')) # Redirect after successful login
        
        # If login fails, show an error message
        flash('Invalid username or password')

    return render_template('login.html')

# A simple protected generator page
@auth_bp.route('/generator')
@login_required
def generator():
    return "<h1>Welcome to the Admin generator!</h1> <a href='/auth/logout'>Logout</a>"

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))