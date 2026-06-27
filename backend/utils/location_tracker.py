"""
Real-time User Location Tracker
Continuously extracts and updates user location from multiple sources
"""

from geopy.geocoders import Nominatim
from utils.location_mapper import (
    format_location_for_complaint,
    validate_location_bounds,
    find_nearest_ward
)
import json
import time
from datetime import datetime


class LocationTracker:
    """
    Real-time location tracking with continuous updates.
    Supports: Browser Geolocation API, Google Maps, Image Geotag
    """
    
    def __init__(self):
        self.current_location = None
        self.location_history = []
        self.last_update = None
        self.update_interval = 5  # seconds
        
    
    def update_location_from_gps(self, latitude, longitude, accuracy=None):
        """
        Update location from GPS coordinates (real-time from device).
        Called continuously as user moves.
        
        Args:
            latitude: Current latitude
            longitude: Current longitude
            accuracy: GPS accuracy in meters (optional)
        
        Returns:
            dict: Updated location data
        """
        timestamp = datetime.now()
        
        # Validate bounds
        validation = validate_location_bounds(latitude, longitude)
        if not validation["valid"]:
            return {
                "success": False,
                "message": validation["message"]
            }
        
        # Format location
        location_data = format_location_for_complaint(latitude, longitude)
        location_data["source"] = "gps_continuous"
        location_data["timestamp"] = timestamp.isoformat()
        
        if accuracy:
            location_data["gps_accuracy_meters"] = accuracy
        
        # Update current location
        self.current_location = location_data
        self.last_update = timestamp
        
        # Track history
        self.location_history.append({
            "timestamp": timestamp.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "ward": location_data.get("ward", {}).get("ward_name")
        })
        
        return {
            "success": True,
            "location": location_data,
            "message": f"Location updated: {location_data.get('ward', {}).get('ward_name')}"
        }
    
    
    def update_location_from_google_maps(self, latitude, longitude, address, place_id=None):
        """
        Update location from Google Maps selection.
        User clicks on map and location is selected.
        
        Args:
            latitude: Selected latitude
            longitude: Selected longitude
            address: Human-readable address from Google Maps
            place_id: Google Maps place ID (optional)
        
        Returns:
            dict: Updated location data
        """
        timestamp = datetime.now()
        
        # Validate bounds
        validation = validate_location_bounds(latitude, longitude)
        if not validation["valid"]:
            return {
                "success": False,
                "message": validation["message"]
            }
        
        # Format location
        location_data = format_location_for_complaint(latitude, longitude)
        location_data["source"] = "google_maps"
        location_data["timestamp"] = timestamp.isoformat()
        location_data["address"]["google_address"] = address
        location_data["address"]["place_id"] = place_id
        
        # Update current location
        self.current_location = location_data
        self.last_update = timestamp
        
        # Track history
        self.location_history.append({
            "timestamp": timestamp.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "address": address,
            "source": "google_maps"
        })
        
        return {
            "success": True,
            "location": location_data,
            "message": f"Location selected: {address}"
        }
    
    
    def update_location_from_geotag(self, geotag_data):
        """
        Update location from image geotag.
        
        Args:
            geotag_data: GPS data extracted from image EXIF
        
        Returns:
            dict: Updated location data
        """
        if not geotag_data:
            return {
                "success": False,
                "message": "No geotag data provided"
            }
        
        latitude = geotag_data.get("latitude")
        longitude = geotag_data.get("longitude")
        
        if not latitude or not longitude:
            return {
                "success": False,
                "message": "Invalid geotag coordinates"
            }
        
        timestamp = datetime.now()
        
        # Validate bounds
        validation = validate_location_bounds(latitude, longitude)
        if not validation["valid"]:
            return {
                "success": False,
                "message": validation["message"]
            }
        
        # Format location
        location_data = format_location_for_complaint(latitude, longitude)
        location_data["source"] = "image_geotag"
        location_data["timestamp"] = timestamp.isoformat()
        location_data["geotag_metadata"] = {
            "altitude": geotag_data.get("altitude"),
            "image_timestamp": geotag_data.get("timestamp"),
            "accuracy": geotag_data.get("accuracy_meters", 5)
        }
        
        # Update current location
        self.current_location = location_data
        self.last_update = timestamp
        
        # Track history
        self.location_history.append({
            "timestamp": timestamp.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "source": "image_geotag",
            "ward": location_data.get("ward", {}).get("ward_name")
        })
        
        return {
            "success": True,
            "location": location_data,
            "message": f"Location extracted from image: {location_data.get('ward', {}).get('ward_name')}"
        }
    
    
    def get_current_location(self):
        """Get the most recent location."""
        if not self.current_location:
            return {
                "success": False,
                "message": "No location captured yet"
            }
        
        return {
            "success": True,
            "location": self.current_location,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
    
    
    def get_location_history(self, limit=10):
        """Get recent location history."""
        return {
            "history": self.location_history[-limit:],
            "total_updates": len(self.location_history)
        }
    
    
    def clear_location(self):
        """Clear current location data."""
        self.current_location = None
        self.location_history = []
        self.last_update = None
        return {"success": True, "message": "Location cleared"}


# Global tracker instance (shared across requests)
location_tracker = LocationTracker()
