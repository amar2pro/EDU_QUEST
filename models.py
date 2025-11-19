from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(80), nullable=True)
    contact = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    accessibility = db.Column(db.Text, nullable=True)
    fee_structure = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    
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

class Principal(db.Model):
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
    is_active = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    school = db.relationship('School', backref=db.backref('principal', uselist=False))

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
            "email_verified": self.email_verified,
            "school_name": self.school.name if self.school else None
        }

class MeetingBooking(db.Model):
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
    
    # ✅ FIXED: Use DIFFERENT backref names to avoid conflict
    school = db.relationship('School', backref=db.backref('school_meetings', lazy=True))
    principal = db.relationship('Principal', backref=db.backref('principal_meetings', lazy=True))

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
            "created_at": self.created_at.isoformat(),
            "school_name": self.school.name if self.school else None,
            "principal_name": self.principal.name if self.principal else None
        }