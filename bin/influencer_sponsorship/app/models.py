from flask_login import UserMixin
from datetime import datetime
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin', 'sponsor', 'influencer'
    sponsor = db.relationship('Sponsor', backref='user', uselist=False)
    influencer = db.relationship('Influencer', backref='user', uselist=False)
    flagged = db.Column(db.Boolean, default=False)  # Add this line

    influencer = db.relationship('Influencer', backref='user', uselist=False)

class Sponsor(db.Model):
    __tablename__ = 'sponsors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(150))
    industry = db.Column(db.String(100))
    budget = db.Column(db.Float)

class Influencer(db.Model):
    __tablename__ = 'influencers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(100))
    niche = db.Column(db.String(100))
    reach = db.Column(db.Integer)

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Float)
    visibility = db.Column(db.String(50))
    goals = db.Column(db.String(150))
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.id'), nullable=False)
    
    # Relationship
    sponsor = db.relationship('Sponsor', backref='campaigns')

class AdRequest(db.Model):
    __tablename__ = 'ad_requests'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    messages = db.Column(db.Text)
    requirements = db.Column(db.Text)
    payment_amount = db.Column(db.Float)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    campaign = db.relationship('Campaign', backref='ad_requests')
    influencer = db.relationship('User', foreign_keys=[influencer_id], backref='received_ad_requests')
    sponsor = db.relationship('User', foreign_keys=[sponsor_id], backref='sent_ad_requests')

    def __repr__(self):
        return f'<AdRequest {self.id} - Campaign {self.campaign_id}>'
