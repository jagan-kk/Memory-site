from app import login_manager, mongo
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from bson.objectid import ObjectId # Import ObjectId

# This class will act as a wrapper around the user document from MongoDB
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.password_hash = user_data.get('password_hash')
        self.role = user_data.get('role')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# This callback reloads the user object from the user ID stored in the session.
@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None