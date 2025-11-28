from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()



# ✅ CLEAN School model
class School(db.Model):
    __tablename__ = 'school'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(80), nullable=True)
    contact = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    accessibility = db.Column(db.Text, nullable=True)
    fee_structure = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)

    #RELATIONSHIPS
    principals = db.relationship('Principal', backref='school_assoc', cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='school_assoc', cascade='all, delete-orphan')
    meetings = db.relationship('MeetingBooking', backref='school_assoc', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "level": self.level,
            "contact": self.contact,
            "description": self.description,
            "accessibility": self.accessibility,
            "fee_structure": self.fee_structure,
            "image_url": self.image_url
        }

# ✅ CLEAN Feedback model
# ✅ UPDATED Feedback model with principal replies
class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin reply fields
    admin_reply = db.Column(db.Text, nullable=True)
    reply_date = db.Column(db.DateTime, nullable=True)
    
    # Principal reply fields (NEW)
    principal_reply = db.Column(db.Text, nullable=True)
    principal_reply_date = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "school_id": self.school_id,
            "name": self.name,
            "email": self.email,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "admin_reply": self.admin_reply,
            "reply_date": self.reply_date.isoformat() if self.reply_date else None,
            "principal_reply": self.principal_reply,
            "principal_reply_date": self.principal_reply_date.isoformat() if self.principal_reply_date else None
        }

# ✅ CLEAN Principal model
class Principal(db.Model):
    __tablename__ = 'principal'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text)
    qualifications = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    office_hours = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)  # Changed to True for now
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "school_id": self.school_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "bio": self.bio,
            "qualifications": self.qualifications,
            "image_url": self.image_url,
            "office_hours": self.office_hours,
            "is_active": self.is_active,
            "email_verified": self.email_verified
        }

# ✅ CLEAN MeetingBooking model
class MeetingBooking(db.Model):
    __tablename__ = 'meeting_booking'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    principal_id = db.Column(db.Integer, db.ForeignKey('principal.id'), nullable=False)
    user_name = db.Column(db.String(200), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    user_phone = db.Column(db.String(20))
    purpose = db.Column(db.Text, nullable=False)
    preferred_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    special_requirements = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "school_id": self.school_id,
            "principal_id": self.principal_id,
            "user_name": self.user_name,
            "user_email": self.user_email,
            "user_phone": self.user_phone,
            "purpose": self.purpose,
            "preferred_date": self.preferred_date.isoformat(),
            "status": self.status,
            "special_requirements": self.special_requirements,
            "created_at": self.created_at.isoformat()
        }

# ✅ SIMPLE Admin model
class Admin(db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ✅ SIMPLE User model (NO RELATIONSHIPS FOR NOW)
class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }