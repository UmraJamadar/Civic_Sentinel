from flask import Blueprint, request, jsonify
from utils.location_tracker import location_tracker
from utils.geotag_extractor import extract_gps_from_geotag
import os

location_bp = Blueprint("location", __name__)

UPLOAD_FOLDER = "uploads"


@location_bp.route("/track/gps", methods=["POST"])
def track_gps():
    """
    Real-time GPS location update from device.
    Called continuously as user moves.
    
    Expected JSON:
    {
        "latitude": 15.3647,
        "longitude": 75.1240,
        "accuracy": 5.5
    }
    """
    try:
        data = request.get_json()
        
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        accuracy = data.get("accuracy")
        
        if latitude is None or longitude is None:
            return jsonify({"error": "latitude and longitude required"}), 400
        
        # Update location tracker
        result = location_tracker.update_location_from_gps(latitude, longitude, accuracy)
        
        return jsonify(result), 200 if result["success"] else 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@location_bp.route("/track/google-maps", methods=["POST"])
def track_google_maps():
    """
    Location update from Google Maps selection.
    User selects location on map.
    
    Expected JSON:
    {
        "latitude": 15.3647,
        "longitude": 75.1240,
        "address": "MG Road, Hubli, Karnataka",
        "place_id": "ChIJz-wLXXYF..." (optional)
    }
    """
    try:
        data = request.get_json()
        
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        address = data.get("address", "")
        place_id = data.get("place_id")
        
        if latitude is None or longitude is None:
            return jsonify({"error": "latitude and longitude required"}), 400
        
        # Update location tracker
        result = location_tracker.update_location_from_google_maps(
            latitude, longitude, address, place_id
        )
        
        return jsonify(result), 200 if result["success"] else 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@location_bp.route("/track/geotag", methods=["POST"])
def track_geotag():
    """
    Location update from image geotag.
    Extract location from uploaded image.
    
    Expected: Image file with EXIF GPS data
    """
    try:
        if "image" not in request.files:
            return jsonify({"error": "Image file required"}), 400
        
        image = request.files["image"]
        
        # Save temporarily
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{image.filename}")
        image.save(temp_path)
        
        # Extract geotag
        geotag_data = extract_gps_from_geotag(temp_path)
        
        if not geotag_data:
            os.remove(temp_path)
            return jsonify({
                "error": "No geotag found in image",
                "message": "Image does not have GPS location data. Use manual input instead."
            }), 400
        
        # Update location tracker
        result = location_tracker.update_location_from_geotag(geotag_data)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify(result), 200 if result["success"] else 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@location_bp.route("/current", methods=["GET"])
def get_current_location():
    """Get currently tracked location."""
    result = location_tracker.get_current_location()
    return jsonify(result), 200 if result["success"] else 400


@location_bp.route("/history", methods=["GET"])
def get_location_history():
    """Get location update history."""
    limit = request.args.get("limit", 10, type=int)
    result = location_tracker.get_location_history(limit)
    return jsonify(result), 200


@location_bp.route("/clear", methods=["POST"])
def clear_location():
    """Clear current location tracking."""
    result = location_tracker.clear_location()
    return jsonify(result), 200


@location_bp.route("/status", methods=["GET"])
def location_status():
    """Get location tracking status."""
    current = location_tracker.get_current_location()
    
    return jsonify({
        "tracking_active": current["success"],
        "current_location": current.get("location") if current["success"] else None,
        "last_update": current.get("last_update"),
        "history_count": len(location_tracker.location_history)
    }), 200
