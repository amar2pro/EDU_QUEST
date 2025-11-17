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
    
