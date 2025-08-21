from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, email, password_hash=None, _id=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self._id = _id # MongoDB ObjectId

    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self._id)

    @staticmethod
    def find_by_username(db, username):
        user_data = db.users.find_one({"username": username})
        if user_data:
            return User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                _id=user_data['_id']
            )
        return None

    @staticmethod
    def find_by_id(db, user_id):
        from bson.objectid import ObjectId # Import ObjectId here
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                _id=user_data['_id']
            )
        return None

    @staticmethod
    def create_user(db, username, email, password):
        if User.find_by_username(db, username):
            return None # User already exists

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        result = db.users.insert_one({
            "username": new_user.username,
            "email": new_user.email,
            "password_hash": new_user.password_hash
        })
        new_user._id = result.inserted_id
        return new_user
