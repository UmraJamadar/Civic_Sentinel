from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os
from datetime import datetime


def _convert_to_degrees(gps_coords):
    """
    Convert GPS coordinates from DMS (Degrees, Minutes, Seconds) to decimal degrees.
    """
    try:
        degrees = gps_coords[0]
        minutes = gps_coords[1] / 60.0
        seconds = gps_coords[2] / 3600.0
        return degrees + minutes + seconds
    except (TypeError, IndexError):
        return None


def extract_gps_from_geotag(image_path):
    """
    Extract GPS coordinates from image EXIF geotag data.
    
    Returns:
        dict: {
            "latitude": float,
            "longitude": float,
            "altitude": float or None,
            "timestamp": str or None,
            "source": "image_geotag"
        } 
        or None if no GPS data found
    """
    try:
        image = Image.open(image_path)
        
        # Get EXIF data
        exif_data = image._getexif()
        if not exif_data:
            return None
        
        # Find GPS IFD
        gps_ifd = None
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == "GPSInfo":
                gps_ifd = value
                break
        
        if not gps_ifd:
            return None
        
        # Parse GPS data
        gps_data = {}
        for tag_id, value in gps_ifd.items():
            tag_name = GPSTAGS.get(tag_id, tag_id)
            gps_data[tag_name] = value
        
        # Extract latitude
        lat = None
        if "GPSLatitude" in gps_data:
            lat = _convert_to_degrees(gps_data["GPSLatitude"])
            if "GPSLatitudeRef" in gps_data and gps_data["GPSLatitudeRef"] == "S":
                lat = -lat
        
        # Extract longitude
        lng = None
        if "GPSLongitude" in gps_data:
            lng = _convert_to_degrees(gps_data["GPSLongitude"])
            if "GPSLongitudeRef" in gps_data and gps_data["GPSLongitudeRef"] == "W":
                lng = -lng
        
        # Extract altitude
        altitude = None
        if "GPSAltitude" in gps_data:
            try:
                altitude = float(gps_data["GPSAltitude"][0]) / float(gps_data["GPSAltitude"][1])
            except (TypeError, ZeroDivisionError, IndexError):
                altitude = None
        
        # Extract timestamp
        timestamp = None
        if "GPSDateStamp" in gps_data:
            timestamp = gps_data["GPSDateStamp"]
        
        # Return GPS data if coordinates exist
        if lat is not None and lng is not None:
            return {
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "altitude": round(altitude, 2) if altitude else None,
                "timestamp": timestamp,
                "source": "image_geotag",
                "accuracy_meters": 5  # Typical GPS geotag accuracy
            }
        
        return None
    
    except Exception as e:
        print(f"Error extracting geotag from {image_path}: {str(e)}")
        return None


def get_image_metadata(image_path):
    """
    Extract all EXIF metadata from image including timestamp, camera info, etc.
    
    Returns:
        dict: Complete EXIF metadata
    """
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        
        if not exif_data:
            return {}
        
        metadata = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            try:
                metadata[tag_name] = str(value)
            except:
                pass
        
        return metadata
    
    except Exception as e:
        print(f"Error reading metadata from {image_path}: {str(e)}")
        return {}


def is_geotagged(image_path):
    """
    Check if an image has geotag (GPS) data.
    
    Returns:
        bool: True if image has GPS coordinates
    """
    gps_data = extract_gps_from_geotag(image_path)
    return gps_data is not None
