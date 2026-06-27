import json
import os
import math
from geopy.geocoders import Nominatim


# Load Hubli-Dharwad wards data
WARDS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "hubli_dharwad_wards.json")

try:
    with open(WARDS_FILE, "r") as f:
        WARDS_DATA = json.load(f)
except FileNotFoundError:
    print(f"Warning: {WARDS_FILE} not found. Ward mapping will be limited.")
    WARDS_DATA = None


def _calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in kilometers using Haversine formula.
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def find_nearest_ward(latitude, longitude):
    """
    Find the nearest ward to the given coordinates.
    
    Returns:
        dict: Ward information including ward_id, ward_name, zone_id, etc.
    """
    if not WARDS_DATA or not WARDS_DATA.get("wards"):
        return None
    
    nearest_ward = None
    min_distance = float('inf')
    
    for ward in WARDS_DATA["wards"]:
        distance = _calculate_distance(
            latitude, 
            longitude,
            ward["latitude"],
            ward["longitude"]
        )
        
        if distance < min_distance:
            min_distance = distance
            nearest_ward = ward
    
    return nearest_ward


def find_zone_by_id(zone_id):
    """
    Find zone information by zone ID.
    """
    if not WARDS_DATA:
        return None
    
    for zone in WARDS_DATA.get("zones", []):
        if zone["zone_id"] == zone_id:
            return zone
    
    return None


def find_department_for_issue(issue_type, zone_id=None):
    """
    Find the appropriate department for the given issue type.
    
    Args:
        issue_type: "pothole", "garbage", "water_leak", etc.
        zone_id: Optional zone ID for routing
    
    Returns:
        dict: Department information
    """
    if not WARDS_DATA:
        return None
    
    issue_mapping = {
        "pothole": "D-002",  # Road & Infrastructure
        "garbage": "D-001",  # Sanitation & Waste Management
        "waste dumping": "D-001",  # Sanitation & Waste Management
        "illegal dumping": "D-001",  # Sanitation & Waste Management
        "water leak": "D-003",  # Water Supply
        "sewage": "D-003",  # Water Supply
        "drain": "D-003",  # Water Supply
    }
    
    # Find matching department
    dept_id = None
    for key, value in issue_mapping.items():
        if key in issue_type.lower():
            dept_id = value
            break
    
    # Default to Road & Infrastructure if no match
    if not dept_id:
        dept_id = "D-002"
    
    for dept in WARDS_DATA.get("departments", []):
        if dept["dept_id"] == dept_id:
            return dept
    
    return None


def get_location_info(latitude, longitude):
    """
    Get complete location information for given coordinates.
    
    Returns:
        dict: {
            "coordinates": {...},
            "ward": {...},
            "zone": {...},
            "address": {...}
        }
    """
    result = {
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude
        },
        "ward": None,
        "zone": None,
        "address": {}
    }
    
    # Find nearest ward
    ward = find_nearest_ward(latitude, longitude)
    if ward:
        result["ward"] = {
            "ward_id": ward["ward_id"],
            "ward_name": ward["ward_name"],
            "main_areas": ward["main_areas"]
        }
        
        # Get zone info
        zone = find_zone_by_id(ward["zone_id"])
        if zone:
            result["zone"] = {
                "zone_id": zone["zone_id"],
                "zone_name": zone["zone_name"],
                "department": zone["department"]
            }
    
    # Reverse geocode using Nominatim
    try:
        geolocator = Nominatim(user_agent="civic_sentinel_hubli")
        location = geolocator.reverse(f"{latitude}, {longitude}", language="en")
        
        if location:
            address_parts = location.address.split(",")
            result["address"] = {
                "full_address": location.address,
                "city": "Hubli-Dharwad",
                "state": "Karnataka",
                "country": "India"
            }
    except Exception as e:
        print(f"Error in reverse geocoding: {str(e)}")
    
    return result


def validate_location_bounds(latitude, longitude):
    """
    Validate if coordinates are within Hubli-Dharwad city bounds.
    
    Returns:
        dict: {
            "valid": bool,
            "message": str
        }
    """
    if not WARDS_DATA:
        return {"valid": True, "message": "Ward data not available for validation"}
    
    bounds = WARDS_DATA.get("city_bounds", {})
    
    north = bounds.get("north", 15.5)
    south = bounds.get("south", 15.2)
    east = bounds.get("east", 75.3)
    west = bounds.get("west", 74.9)
    
    if south <= latitude <= north and west <= longitude <= east:
        return {
            "valid": True,
            "message": "Location is within Hubli-Dharwad city"
        }
    else:
        return {
            "valid": False,
            "message": f"Location ({latitude}, {longitude}) is outside Hubli-Dharwad city bounds"
        }


def format_location_for_complaint(latitude, longitude):
    """
    Format location data for storing in complaint.
    
    Returns:
        dict: Structured location data ready for MongoDB
    """
    location_info = get_location_info(latitude, longitude)
    validation = validate_location_bounds(latitude, longitude)
    
    return {
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
            "type": "Point"
        },
        "address": location_info["address"],
        "ward": location_info["ward"],
        "zone": location_info["zone"],
        "city": "Hubli-Dharwad",
        "state": "Karnataka",
        "country": "India",
        "within_city_bounds": validation["valid"],
        "validation_message": validation["message"]
    }
