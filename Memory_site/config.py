import os

class Config:
    # A secret key is required for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-you-should-change'
    
    # --- YOUR UPDATED MONGODB CONFIGURATION ---
    # This now uses the specific connection details for your Cluster0.
    MONGO_URI = os.environ.get('MONGO_URI') or \
        'mongodb+srv://jagankk:Jagankkstm23@cluster0.kqm7txf.mongodb.net/arProjectDB?retryWrites=true&w=majority&appName=Cluster0'