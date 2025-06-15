from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import os
import base64
import secrets

db = SQLAlchemy()

# Encryption key for API keys
def get_encryption_key():
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        key = Fernet.generate_key()
        print(f"Generated encryption key: {key.decode()}")
        print("Add this to your .env file as ENCRYPTION_KEY")
    else:
        key = key.encode()
    return key

def encrypt_api_key(api_key):
    if not api_key:
        return None
    f = Fernet(get_encryption_key())
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key):
    if not encrypted_key:
        return None
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_key.encode()).decode()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # API Keys (encrypted)
    openai_api_key = db.Column(db.Text)
    anthropic_api_key = db.Column(db.Text)
    
    # Nutgraf API key for external access
    nutgraf_api_key = db.Column(db.String(64), unique=True, index=True)
    api_calls_made = db.Column(db.Integer, default=0)
    api_calls_limit = db.Column(db.Integer, default=1000)  # Default limit per month
    
    # User preferences
    default_length = db.Column(db.String(20), default='standard')
    default_tone = db.Column(db.String(20), default='neutral')
    default_format = db.Column(db.String(20), default='prose')
    default_model = db.Column(db.String(50), default='gpt-3.5-turbo')
    
    # Relationships
    summaries = db.relationship('Summary', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_openai_key(self, api_key):
        self.openai_api_key = encrypt_api_key(api_key)
    
    def get_openai_key(self):
        return decrypt_api_key(self.openai_api_key)
    
    def set_anthropic_key(self, api_key):
        self.anthropic_api_key = encrypt_api_key(api_key)
    
    def get_anthropic_key(self):
        return decrypt_api_key(self.anthropic_api_key)
    
    def generate_api_key(self):
        """Generate a new API key for external access"""
        self.nutgraf_api_key = 'ng_' + secrets.token_urlsafe(32)
        return self.nutgraf_api_key
    
    def reset_api_usage(self):
        """Reset API usage counter (typically called monthly)"""
        self.api_calls_made = 0
    
    def increment_api_usage(self):
        """Increment API usage counter"""
        self.api_calls_made += 1
    
    def can_make_api_call(self):
        """Check if user can make another API call"""
        return self.api_calls_made < self.api_calls_limit

class Summary(db.Model):
    __tablename__ = 'summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Original article metadata
    url = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text)
    author = db.Column(db.String(255))
    publication_date = db.Column(db.DateTime)
    original_text = db.Column(db.Text)
    
    # Summary content and settings
    summary_text = db.Column(db.Text, nullable=False)
    length_setting = db.Column(db.String(20))  # brief, standard, in_depth, custom
    tone_setting = db.Column(db.String(20))    # neutral, conversational, professional
    format_setting = db.Column(db.String(20))  # prose, bullets
    model_used = db.Column(db.String(50))      # gpt-4, gpt-3.5-turbo, claude-3, etc.
    word_count = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = db.relationship('SummaryTag', backref='summary', lazy=True, cascade='all, delete-orphan')
    
    def get_tag_names(self):
        return [st.tag.name for st in self.tags]

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    summaries = db.relationship('SummaryTag', backref='tag', lazy=True)

class SummaryTag(db.Model):
    __tablename__ = 'summary_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    summary_id = db.Column(db.Integer, db.ForeignKey('summaries.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate tags on same summary
    __table_args__ = (db.UniqueConstraint('summary_id', 'tag_id'),)