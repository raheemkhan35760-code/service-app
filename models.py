from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    description = Column(Text)
    full_description = Column(Text)
    icon = Column(String)
    base_price = Column(Float)
    emergency_price = Column(Float)
    estimated_time = Column(String)
    rating = Column(Float, default=4.8)
    total_bookings = Column(Integer, default=0)
    is_emergency_available = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    features = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.now)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    name = Column(String)
    description = Column(Text)
    price = Column(Float)
    original_price = Column(Float)
    discount_percentage = Column(Integer)
    image_url = Column(String)
    rating = Column(Float, default=4.5)
    stock_quantity = Column(Integer, default=10)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class Technician(Base):
    __tablename__ = "technicians"
    
    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(String, unique=True)
    name = Column(String)
    phone = Column(String)
    email = Column(String)
    photo_url = Column(String)
    service_category = Column(String)
    experience_years = Column(Integer)
    rating = Column(Float, default=4.8)
    total_jobs = Column(Integer, default=0)
    current_latitude = Column(Float, default=28.6139)
    current_longitude = Column(Float, default=77.2090)
    is_available = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(String, unique=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    
    customer_name = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    
    preferred_date = Column(DateTime)
    preferred_time = Column(String)
    problem_description = Column(Text)
    is_emergency = Column(Boolean, default=False)
    uploaded_files = Column(Text)  # JSON array
    
    status = Column(String, default="pending")  # pending, confirmed, technician_assigned, en_route, arrived, in_progress, completed
    
    estimated_price = Column(Float)
    final_price = Column(Float, nullable=True)
    payment_status = Column(String, default="pending")
    
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

class TechnicianTracking(Base):
    __tablename__ = "technician_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    technician_id = Column(Integer, ForeignKey("technicians.id"))
    
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    customer_latitude = Column(Float)
    customer_longitude = Column(Float)
    
    status = Column(String, default="assigned")  # assigned, en_route, arrived, completed
    last_updated = Column(DateTime, default=datetime.now)

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    customer_name = Column(String)
    rating = Column(Integer)
    comment = Column(Text)
    service_name = Column(String)
    is_emergency = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    message = Column(Text)
    is_emergency = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
