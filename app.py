from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import uuid
import os
from pydantic import BaseModel, EmailStr
import asyncio

# Import custom modules
from database import get_db, engine
import models
import schemas
from auth import get_password_hash, verify_password, create_access_token
from file_handler import save_uploaded_file, get_file_url
from location_tracker import calculate_distance, get_eta, update_technician_position
from notifications import send_sms, send_email, send_whatsapp_message

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="HomeServe Pro API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager for real-time tracking
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, booking_id: str):
        await websocket.accept()
        self.active_connections[booking_id] = websocket
    
    def disconnect(self, booking_id: str):
        if booking_id in self.active_connections:
            del self.active_connections[booking_id]
    
    async def send_update(self, booking_id: str, data: dict):
        if booking_id in self.active_connections:
            try:
                await self.active_connections[booking_id].send_json(data)
            except:
                self.disconnect(booking_id)

manager = ConnectionManager()

# ==================== SERVICES ENDPOINTS ====================

@app.get("/api/services")
async def get_all_services(db: Session = Depends(get_db)):
    """Get all available services - matches frontend loadServices()"""
    services = db.query(models.Service).filter(models.Service.is_active == True).all()
    
    return {
        "success": True,
        "services": [
            {
                "id": service.id,
                "name": service.name,
                "category": service.category,
                "description": service.description,
                "icon": service.icon,
                "basePrice": service.base_price,
                "emergencyPrice": service.emergency_price,
                "estimatedTime": service.estimated_time,
                "rating": service.rating,
                "totalBookings": service.total_bookings,
                "isEmergencyAvailable": service.is_emergency_available
            }
            for service in services
        ]
    }

@app.get("/api/services/{service_id}")
async def get_service_detail(service_id: int, db: Session = Depends(get_db)):
    """Get detailed service information with products"""
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Get related products
    products = db.query(models.Product).filter(
        models.Product.service_id == service_id,
        models.Product.is_available == True
    ).all()
    
    return {
        "success": True,
        "service": {
            "id": service.id,
            "name": service.name,
            "category": service.category,
            "description": service.description,
            "fullDescription": service.full_description,
            "icon": service.icon,
            "basePrice": service.base_price,
            "emergencyPrice": service.emergency_price,
            "estimatedTime": service.estimated_time,
            "rating": service.rating,
            "totalBookings": service.total_bookings,
            "features": json.loads(service.features) if service.features else []
        },
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "image": product.image_url,
                "rating": product.rating,
                "inStock": product.stock_quantity > 0
            }
            for product in products
        ]
    }

# ==================== BOOKING ENDPOINTS ====================

@app.post("/api/bookings/create")
async def create_booking(
    service_id: int = Form(...),
    customer_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    preferred_date: str = Form(...),
    preferred_time: str = Form(...),
    problem_description: str = Form(...),
    is_emergency: bool = Form(False),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Create new booking with file uploads - matches booking form submission"""
    
    # Handle file uploads (images/videos)
    uploaded_files = []
    if files:
        for file in files:
            if file.filename:
                file_path = await save_uploaded_file(file)
                uploaded_files.append(file_path)
    
    # Create booking
    booking = models.Booking(
        booking_id=str(uuid.uuid4())[:8].upper(),
        service_id=service_id,
        customer_name=customer_name,
        phone=phone,
        email=email,
        address=address,
        latitude=latitude or 28.6139,  # Default Delhi coordinates
        longitude=longitude or 77.2090,
        preferred_date=datetime.strptime(preferred_date, "%Y-%m-%d"),
        preferred_time=preferred_time,
        problem_description=problem_description,
        is_emergency=is_emergency,
        uploaded_files=json.dumps(uploaded_files),
        status="confirmed",
        created_at=datetime.now()
    )
    
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    # Find nearest available technician
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    technician = find_nearest_technician(db, service.category, latitude, longitude)
    
    if technician:
        # Assign technician
        booking.technician_id = technician.id
        booking.status = "technician_assigned"
        db.commit()
        
        # Create tracking record
        tracking = models.TechnicianTracking(
            booking_id=booking.id,
            technician_id=technician.id,
            current_latitude=technician.current_latitude,
            current_longitude=technician.current_longitude,
            customer_latitude=latitude,
            customer_longitude=longitude,
            status="assigned"
        )
        db.add(tracking)
        db.commit()
        
        # Send notifications
        await send_sms(phone, f"Booking confirmed! Your technician {technician.name} will arrive soon. Track: https://homeservepro.com/track/{booking.booking_id}")
        await send_email(email, "Booking Confirmed", f"Your booking #{booking.booking_id} is confirmed.")
        
        if is_emergency:
            await send_sms(technician.phone, f"EMERGENCY BOOKING! {service.name} at {address}. Customer: {phone}")
    
    return {
        "success": True,
        "message": "Booking created successfully",
        "bookingId": booking.booking_id,
        "booking": {
            "id": booking.booking_id,
            "status": booking.status,
            "customerName": booking.customer_name,
            "phone": booking.phone,
            "address": booking.address,
            "serviceName": service.name,
            "preferredDate": booking.preferred_date.strftime("%Y-%m-%d"),
            "preferredTime": booking.preferred_time,
            "isEmergency": booking.is_emergency,
            "technician": {
                "name": technician.name,
                "phone": technician.phone,
                "photo": technician.photo_url,
                "experience": technician.experience_years,
                "technicianId": technician.technician_id
            } if technician else None
        }
    }

@app.get("/api/bookings/{booking_id}")
async def get_booking_details(booking_id: str, db: Session = Depends(get_db)):
    """Get booking details by booking ID"""
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    technician = db.query(models.Technician).filter(models.Technician.id == booking.technician_id).first()
    
    return {
        "success": True,
        "booking": {
            "id": booking.booking_id,
            "status": booking.status,
            "customerName": booking.customer_name,
            "phone": booking.phone,
            "email": booking.email,
            "address": booking.address,
            "serviceName": service.name if service else "",
            "preferredDate": booking.preferred_date.strftime("%Y-%m-%d"),
            "preferredTime": booking.preferred_time,
            "problemDescription": booking.problem_description,
            "isEmergency": booking.is_emergency,
            "uploadedFiles": json.loads(booking.uploaded_files) if booking.uploaded_files else [],
            "createdAt": booking.created_at.isoformat(),
            "technician": {
                "name": technician.name,
                "phone": technician.phone,
                "photo": technician.photo_url,
                "experience": technician.experience_years,
                "rating": technician.rating,
                "technicianId": technician.technician_id
            } if technician else None
        }
    }

# ==================== TRACKING ENDPOINTS ====================

@app.websocket("/ws/tracking/{booking_id}")
async def websocket_tracking(websocket: WebSocket, booking_id: str, db: Session = Depends(get_db)):
    """WebSocket for real-time technician tracking - matches frontend tracking"""
    await manager.connect(websocket, booking_id)
    
    try:
        booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
        
        if not booking:
            await websocket.close()
            return
        
        while True:
            # Get latest tracking info
            tracking = db.query(models.TechnicianTracking).filter(
                models.TechnicianTracking.booking_id == booking.id
            ).first()
            
            if tracking:
                distance = calculate_distance(
                    tracking.current_latitude,
                    tracking.current_longitude,
                    tracking.customer_latitude,
                    tracking.customer_longitude
                )
                
                eta = get_eta(distance)
                
                # Send update to frontend
                await manager.send_update(booking_id, {
                    "latitude": tracking.current_latitude,
                    "longitude": tracking.current_longitude,
                    "distance": round(distance, 2),
                    "eta": eta,
                    "status": tracking.status,
                    "lastUpdated": tracking.last_updated.isoformat()
                })
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(booking_id)

@app.get("/api/tracking/{booking_id}")
async def get_tracking_info(booking_id: str, db: Session = Depends(get_db)):
    """Get current tracking information"""
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    tracking = db.query(models.TechnicianTracking).filter(
        models.TechnicianTracking.booking_id == booking.id
    ).first()
    
    technician = db.query(models.Technician).filter(
        models.Technician.id == booking.technician_id
    ).first()
    
    if not tracking or not technician:
        return {"success": False, "message": "Tracking not available"}
    
    distance = calculate_distance(
        tracking.current_latitude,
        tracking.current_longitude,
        tracking.customer_latitude,
        tracking.customer_longitude
    )
    
    eta = get_eta(distance)
    
    return {
        "success": True,
        "tracking": {
            "technicianName": technician.name,
            "technicianPhone": technician.phone,
            "technicianPhoto": technician.photo_url,
            "technicianId": technician.technician_id,
            "experience": technician.experience_years,
            "currentLatitude": tracking.current_latitude,
            "currentLongitude": tracking.current_longitude,
            "distance": round(distance, 2),
            "eta": eta,
            "status": tracking.status,
            "timeline": [
                {"event": "Booking confirmed", "time": booking.created_at.strftime("%I:%M %p"), "completed": True},
                {"event": "Technician assigned", "time": (booking.created_at + timedelta(minutes=2)).strftime("%I:%M %p"), "completed": True},
                {"event": "Technician started journey", "time": (booking.created_at + timedelta(minutes=15)).strftime("%I:%M %p"), "completed": tracking.status in ["en_route", "arrived", "completed"]},
                {"event": f"Currently {distance:.1f} km away", "time": datetime.now().strftime("%I:%M %p"), "completed": False}
            ]
        }
    }

@app.post("/api/technician/update-location")
async def update_technician_location(
    technician_id: int = Form(...),
    booking_id: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: Session = Depends(get_db)
):
    """Technician updates their location"""
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    tracking = db.query(models.TechnicianTracking).filter(
        models.TechnicianTracking.booking_id == booking.id
    ).first()
    
    if tracking:
        tracking.current_latitude = latitude
        tracking.current_longitude = longitude
        tracking.last_updated = datetime.now()
        
        distance = calculate_distance(latitude, longitude, tracking.customer_latitude, tracking.customer_longitude)
        
        # Update status based on distance
        if distance < 0.1:  # Less than 100 meters
            tracking.status = "arrived"
            booking.status = "arrived"
        elif tracking.status != "arrived":
            tracking.status = "en_route"
            booking.status = "en_route"
        
        db.commit()
    
    return {"success": True, "message": "Location updated"}

# ==================== REVIEWS ENDPOINTS ====================

@app.get("/api/reviews")
async def get_all_reviews(limit: int = 6, db: Session = Depends(get_db)):
    """Get customer reviews - matches frontend reviews display"""
    reviews = db.query(models.Review).order_by(models.Review.created_at.desc()).limit(limit).all()
    
    return {
        "success": True,
        "reviews": [
            {
                "id": review.id,
                "customerName": review.customer_name,
                "rating": review.rating,
                "comment": review.comment,
                "serviceName": review.service_name,
                "date": review.created_at.strftime("%d %b %Y"),
                "daysAgo": (datetime.now() - review.created_at).days,
                "verified": review.is_verified,
                "isEmergency": review.is_emergency
            }
            for review in reviews
        ]
    }

@app.post("/api/reviews/create")
async def create_review(
    booking_id: str = Form(...),
    rating: int = Form(...),
    comment: str = Form(...),
    db: Session = Depends(get_db)
):
    """Submit customer review"""
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    
    review = models.Review(
        booking_id=booking.id,
        customer_name=booking.customer_name,
        rating=rating,
        comment=comment,
        service_name=service.name if service else "",
        is_emergency=booking.is_emergency,
        is_verified=True,
        created_at=datetime.now()
    )
    
    db.add(review)
    db.commit()
    
    # Update service rating
    if service:
        all_reviews = db.query(models.Review).filter(models.Review.service_name == service.name).all()
        avg_rating = sum([r.rating for r in all_reviews]) / len(all_reviews)
        service.rating = round(avg_rating, 1)
        db.commit()
    
    return {"success": True, "message": "Review submitted successfully"}

# ==================== CONTACT ENDPOINTS ====================

@app.post("/api/contact/send")
async def send_contact_message(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...),
    is_emergency: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Handle contact form submission"""
    contact = models.ContactMessage(
        name=name,
        email=email,
        phone=phone,
        message=message,
        is_emergency=is_emergency,
        created_at=datetime.now()
    )
    
    db.add(contact)
    db.commit()
    
    # Send notification to admin
    if is_emergency:
        await send_sms("+919876543210", f"EMERGENCY CONTACT: {name} - {phone}: {message}")
    
    await send_email(email, "Message Received", "We received your message and will respond within 24-48 hours.")
    
    return {"success": True, "message": "Message sent successfully"}

@app.get("/api/contact/info")
async def get_contact_info():
    """Get company contact information"""
    return {
        "success": True,
        "contactInfo": {
            "emergencyHotline": {
                "number": "+91 1800 123 456",
                "description": "Toll-Free • Always Available"
            },
            "customerCare": {
                "number": "+91 98765 43210",
                "description": "10 AM - 8 PM Daily"
            },
            "whatsapp": {
                "number": "+91 98765 11223",
                "description": "Quick Chat Response"
            },
            "email": {
                "address": "support@homeservepro.com",
                "description": "24-48 hrs response"
            }
        }
    }

# ==================== PRODUCTS ENDPOINTS ====================

@app.get("/api/products/{service_id}")
async def get_products_by_service(service_id: int, db: Session = Depends(get_db)):
    """Get recommended products for a service"""
    products = db.query(models.Product).filter(
        models.Product.service_id == service_id,
        models.Product.is_available == True
    ).limit(6).all()
    
    return {
        "success": True,
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "originalPrice": product.original_price,
                "discount": product.discount_percentage,
                "image": product.image_url,
                "rating": product.rating,
                "inStock": product.stock_quantity > 0
            }
            for product in products
        ]
    }

# ==================== HELPER FUNCTIONS ====================

def find_nearest_technician(db: Session, service_category: str, lat: float, lon: float):
    """Find nearest available technician"""
    technicians = db.query(models.Technician).filter(
        models.Technician.service_category == service_category,
        models.Technician.is_available == True
    ).all()
    
    if not technicians:
        return None
    
    nearest = None
    min_distance = float('inf')
    
    for tech in technicians:
        distance = calculate_distance(tech.current_latitude, tech.current_longitude, lat, lon)
        if distance < min_distance:
            min_distance = distance
            nearest = tech
    
    return nearest

# ==================== STATISTICS ====================

@app.get("/api/stats")
async def get_platform_stats(db: Session = Depends(get_db)):
    """Get platform statistics"""
    total_bookings = db.query(models.Booking).count()
    total_customers = db.query(models.Booking).distinct(models.Booking.phone).count()
    total_technicians = db.query(models.Technician).count()
    avg_rating = db.query(models.Review).with_entities(db.func.avg(models.Review.rating)).scalar()
    
    return {
        "success": True,
        "stats": {
            "totalBookings": total_bookings,
            "totalCustomers": total_customers,
            "activeTechnicians": total_technicians,
            "averageRating": round(avg_rating or 4.8, 1),
            "emergencyResponseTime": "12-18 minutes"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
