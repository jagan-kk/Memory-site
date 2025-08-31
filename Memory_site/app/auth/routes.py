from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required
from app import mongo
from app.models import User

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
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
                # --- CHANGE THIS LINE ---
                return redirect(url_for('admin.dashboard')) # Redirect to admin dashboard
                # -----------------------
        
        # If login fails, show an error message
        flash('Invalid username or password')

    return render_template('login.html')

# A simple protected dashboard page
@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return "<h1>Welcome to the Admin Dashboard!</h1> <a href='/auth/logout'>Logout</a>"

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))