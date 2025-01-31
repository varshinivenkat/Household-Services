from .database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'Users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)
    
    customer = db.relationship(
        'Customer',
        back_populates='user',
        uselist=False,
        cascade="all, delete-orphan"  
    )
    professional = db.relationship(
        'Professional',
        back_populates='user',
        uselist=False,
        cascade="all, delete-orphan"  
    )

class Customer(db.Model):
    __tablename__ = 'Customers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    phone = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    is_blocked = db.Column(db.Boolean, default = False)
    # Relationships
    user = db.relationship('User', back_populates='customer')
    service_requests = db.relationship(
        'ServiceRequest',
        back_populates='customer',
        cascade="all, delete-orphan"  
    )
    reviews = db.relationship(
        'Review',
        back_populates='customer',
        cascade="all, delete-orphan"  
    )

class Professional(db.Model):
    __tablename__ = 'Professionals'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id', ondelete="CASCADE"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('Services.id', ondelete="SET NULL"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    phone = db.Column(db.Text, nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_verified = db.Column(db.Text, default=False)
    documents_path = db.Column(db.Text)
    average_rating = db.Column(db.Numeric(3, 2), default=0.0)
    is_blocked = db.Column(db.Boolean, default = False)
    location = db.Column(db.Text, nullable = False)
    pincode = db.Column(db.Integer, nullable = False)
    
    # Relationships
    user = db.relationship('User', back_populates='professional')
    service = db.relationship('Service', back_populates='professionals')
    service_requests = db.relationship(
        'ServiceRequest',
        back_populates='professional',
        cascade="all, delete-orphan"  
    )
    reviews = db.relationship(
        'Review',
        back_populates='professional',
        cascade="all, delete-orphan" 
    )
    
class Service(db.Model):
    __tablename__ = 'Services'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False, unique=True)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=False)
    time_required = db.Column(db.Integer, nullable=False)  
    category = db.Column(db.Text, nullable = False)
    
    # Relationships
    professionals = db.relationship(
        'Professional',
        back_populates='service',
        cascade="all, delete-orphan"  
    )
    service_requests = db.relationship(
        'ServiceRequest',
        back_populates='service',
        cascade="all, delete-orphan"  
    )

class ServiceRequest(db.Model):
    __tablename__ = 'Service_Requests'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id', ondelete="CASCADE"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('Services.id', ondelete="CASCADE"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('Professionals.id', ondelete="CASCADE"), nullable=False)
    request_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)
    is_completed_professional = db.Column(db.Boolean(20), nullable=False)
    is_completed_customer = db.Column(db.Boolean(20), nullable=False)
    rating = db.Column(db.Numeric(3, 2))
   
    customer = db.relationship('Customer', back_populates='service_requests')
    service = db.relationship('Service', back_populates='service_requests')
    professional = db.relationship('Professional', back_populates='service_requests')
    review = db.relationship(
        'Review',
        back_populates='service_request',
        cascade="all, delete-orphan",  
        uselist=False
    )


class Review(db.Model):
    __tablename__ = 'Reviews'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(db.Integer, db.ForeignKey('Service_Requests.id', ondelete="CASCADE"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id', ondelete="CASCADE"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('Professionals.id', ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Numeric(3, 2), nullable=False)
    review_text = db.Column(db.Text)

    service_request = db.relationship('ServiceRequest', back_populates='review')
    customer = db.relationship('Customer', back_populates='reviews')
    professional = db.relationship('Professional', back_populates='reviews')
