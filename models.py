from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class User:
    def __init__(self):
        # Get MongoDB URI from environment variables
        self.mongo_uri = os.getenv('MONGO_URI')
        if not self.mongo_uri:
            raise ValueError("MongoDB URI not found in environment variables")
        
        # Initialize MongoDB client
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client['accessibility_reports']
        self.users = self.db['users']

    def create_user(self, email, password, name):
        """Create a new user"""
        if self.users.find_one({'email': email}):
            raise ValueError("Email already registered")
        
        user = {
            'email': email,
            'password': generate_password_hash(password),
            'name': name,
            'created_at': datetime.now()
        }
        
        result = self.users.insert_one(user)
        return str(result.inserted_id)

    def authenticate(self, email, password):
        """Authenticate a user"""
        user = self.users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            return {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name']
            }
        return None

    def get_user(self, user_id):
        """Get user by ID"""
        user = self.users.find_one({'_id': user_id})
        if user:
            return {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name']
            }
        return None 