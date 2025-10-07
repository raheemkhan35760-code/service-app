from geopy.distance import geodesic
from datetime import datetime, timedelta

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in kilometers"""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def get_eta(distance_km: float) -> int:
    """Calculate ETA in minutes based on distance"""
    avg_speed_kmh = 30  # Average speed in city
    time_hours = distance_km / avg_speed_kmh
    time_minutes = int(time_hours * 60)
    return max(time_minutes, 5)  # Minimum 5 minutes

def update_technician_position(db, tracking_id: int, lat: float, lon: float):
    """Update technician's current position"""
    from models import TechnicianTracking
    tracking = db.query(TechnicianTracking).filter(TechnicianTracking.id == tracking_id).first()
    if tracking:
        tracking.current_latitude = lat
        tracking.current_longitude = lon
        tracking.last_updated = datetime.now()
        db.commit()
    return tracking
