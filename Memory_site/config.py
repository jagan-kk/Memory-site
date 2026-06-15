import os

class Config:
    # A secret key is required for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-you-should-change'
    
    # --- YOUR UPDATED MONGODB CONFIGURATION ---
    # This now uses the specific connection details for your Cluster0.
    MONGO_URI = os.environ.get('MONGO_URI') or \
        ''
    MAIL_SERVER = ''
    MAIL_PORT = 
    MAIL_USE_TLS = True
    MAIL_USERNAME = ''
    MAIL_PASSWORD = '' # Use an App Password
    MAIL_DEFAULT_SENDER = ''
