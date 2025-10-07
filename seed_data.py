from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def seed_database():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(models.Service).count() > 0:
        print("Database already seeded")
        return
    
    # Seed Services
    services = [
        {
            "name": "Stove Repair Service", "category": "stove_repair", "icon": "🔥",
            "base_price": 299, "emergency_price": 499, "estimated_time": "45-60 min",
            "description": "Expert gas stove and electric stove repair", "is_emergency_available": True
        },
        {
            "name": "Plumber Services", "category": "plumber", "icon": "🚰",
            "base_price": 349, "emergency_price": 549, "estimated_time": "30-90 min",
            "description": "24/7 emergency plumbing solutions", "is_emergency_available": True
        },
        {
            "name": "Electrician Service", "category": "electrician", "icon": "⚡",
            "base_price": 399, "emergency_price": 599, "estimated_time": "30-60 min",
            "description": "Licensed electricians for all electrical work", "is_emergency_available": True
        },
        {
            "name": "AC Repair & Service", "category": "ac_repair", "icon": "❄️",
            "base_price": 499, "emergency_price": 799, "estimated_time": "60-90 min",
            "description": "All brands AC repair and maintenance", "is_emergency_available": True
        },
        {
            "name": "Washing Machine Repair", "category": "washing_machine", "icon": "🧺",
            "base_price": 349, "emergency_price": 549, "estimated_time": "45-75 min",
            "description": "Front load and top load repair specialists", "is_emergency_available": True
        },
        {
            "name": "Refrigerator Service", "category": "refrigerator", "icon": "🧊",
            "base_price": 449, "emergency_price": 649, "estimated_time": "60-90 min",
            "description": "All brands fridge repair and gas filling", "is_emergency_available": True
        },
        {
            "name": "Carpenter Services", "category": "carpenter", "icon": "🔨",
            "base_price": 299, "emergency_price": 499, "estimated_time": "60-120 min",
            "description": "Furniture repair and installation", "is_emergency_available": False
        },
        {
            "name": "Painting Services", "category": "painter", "icon": "🎨",
            "base_price": 399, "emergency_price": 599, "estimated_time": "2-4 hours",
            "description": "Professional interior and exterior painting", "is_emergency_available": False
        },
        {
            "name": "Pest Control", "category": "pest_control", "icon": "🐛",
            "base_price": 599, "emergency_price": 899, "estimated_time": "90-120 min",
            "description": "Complete pest elimination solutions", "is_emergency_available": True
        },
        {
            "name": "Home Cleaning", "category": "cleaning", "icon": "🧹",
            "base_price": 499, "emergency_price": 699, "estimated_time": "2-3 hours",
            "description": "Deep cleaning and sanitization", "is_emergency_available": False
        },
        {
            "name": "CCTV Installation", "category": "cctv", "icon": "📹",
            "base_price": 799, "emergency_price": 1199, "estimated_time": "2-4 hours",
            "description": "Security camera installation and setup", "is_emergency_available": False
        },
        {
            "name": "Water Purifier Service", "category": "water_purifier", "icon": "💧",
            "base_price": 299, "emergency_price": 499, "estimated_time": "45-60 min",
            "description": "RO and UV purifier service and repair", "is_emergency_available": True
        }
    ]
    
    for service_data in services:
        service = models.Service(**service_data)
        db.add(service)
    
    db.commit()
    
    # Seed Technicians
    technicians = [
        {"technician_id": "HSP-7842", "name": "Rajesh Kumar", "phone": "+919876512345", "email": "rajesh@tech.com",
         "service_category": "stove_repair", "experience_years": 8, "rating": 4.9, "photo_url": "/images/tech1.jpg"},
        {"technician_id": "HSP-5621", "name": "Amit Singh", "phone": "+919876512346", "email": "amit@tech.com",
         "service_category": "plumber", "experience_years": 6, "rating": 4.8, "photo_url": "/images/tech2.jpg"},
        {"technician_id": "HSP-8934", "name": "Suresh Patil", "phone": "+919876512347", "email": "suresh@tech.com",
         "service_category": "electrician", "experience_years": 10, "rating": 4.9, "photo_url": "/images/tech3.jpg"},
    ]
    
    for tech_data in technicians:
        tech = models.Technician(**tech_data)
        db.add(tech)
    
    db.commit()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
