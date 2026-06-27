from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from config import *
from AI.detect import detect_issue
from AI.complaint_generator import generate_complaint
from utils.id_generator import generate_id
from utils.location_tracker import location_tracker
from utils.location_mapper import find_department_for_issue
import datetime
import os

complaint_bp = Blueprint("complaint", __name__)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
complaints = db["complaints"]


@complaint_bp.route("/create", methods=["POST"])
@jwt_required()
def create():
    """
    Create complaint from image using continuously tracked location.
    
    Location is automatically extracted from:
    1. Real-time GPS tracking (background)
    2. Google Maps selection (user click)
    3. Image geotag (image EXIF)
    
    The system automatically uses the most recent location tracked.
    """
    try:
        # Validate image file
        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        image = request.files["image"]
        if image.filename == "":
            return jsonify({"error": "No image selected"}), 400
        
        # Save image
        path = os.path.join(UPLOAD_FOLDER, image.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        image.save(path)
        
        # ========== GET LOCATION FROM TRACKER ==========
        location_result = location_tracker.get_current_location()
        
        if not location_result["success"]:
            return jsonify({
                "error": "Location not available",
                "message": "Please enable GPS, select location on map, or upload geotagged image",
                "hint": "System is continuously tracking your location. Please wait or provide location manually."
            }), 400
        
        location_data = location_result["location"]
        latitude = location_data.get("coordinates", {}).get("latitude")
        longitude = location_data.get("coordinates", {}).get("longitude")
        location_source = location_data.get("source", "unknown")
        
        # ========== DETECT ISSUE ==========
        try:
            detected_issue = detect_issue(path)
        except Exception as e:
            print(f"Detection error: {str(e)}")
            detected_issue = "Unknown"
        
        # ========== GENERATE COMPLAINT REPORT ==========
        description = generate_complaint(
            image_path=path,
            detected_class=detected_issue,
            confidence=0.87
        )
        
        # ========== FIND DEPARTMENT ==========
        dept_info = find_department_for_issue(detected_issue)
        department = dept_info["dept_name"] if dept_info else "General Municipal Department"
        
        # ========== GENERATE COMPLAINT ID ==========
        cid = generate_id()
        
        # ========== CREATE COMPLAINT RECORD ==========
        complaint = {
            "complaint_id": cid,
            "user": get_jwt_identity(),
            "issue_type": detected_issue,
            "description": description,
            "confidence": 0.87,
            "department": department,
            "location": location_data,
            "status": "pending",
            "priority": "medium",
            "timeline": [
                {
                    "status": "Registered",
                    "timestamp": datetime.datetime.now(),
                    "note": f"Complaint registered. Location source: {location_source}"
                }
            ],
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "image_path": path
        }
        
        # ========== STORE IN DATABASE ==========
        result = complaints.insert_one(complaint)
        
        return jsonify({
            "success": True,
            "complaint_id": cid,
            "message": f"Complaint registered successfully from {location_source}",
            "details": {
                "issue_type": detected_issue,
                "location_source": location_source,
                "ward": location_data.get("ward", {}).get("ward_name", "Unknown"),
                "zone": location_data.get("zone", {}).get("zone_name", "Unknown"),
                "assigned_department": department,
                "coordinates": f"{latitude}, {longitude}"
            }
        }), 201
    
    except Exception as e:
        return jsonify({
            "error": f"Error creating complaint: {str(e)}"
        }), 500


@complaint_bp.route("/create-with-location", methods=["POST"])
@jwt_required()
def create_with_explicit_location():
    """
    Create complaint with explicit location provided (fallback).
    Use this if automatic location tracking is unavailable.
    
    Form data:
    - image: Image file
    - latitude: GPS latitude
    - longitude: GPS longitude
    - location_source: "gps" | "google_maps" (optional)
    """
    try:
        # Validate image file
        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        if "latitude" not in request.form or "longitude" not in request.form:
            return jsonify({"error": "latitude and longitude required"}), 400
        
        image = request.files["image"]
        
        # Save image
        path = os.path.join(UPLOAD_FOLDER, image.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        image.save(path)
        
        # Get coordinates
        try:
            latitude = float(request.form.get("latitude"))
            longitude = float(request.form.get("longitude"))
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid latitude/longitude format"}), 400
        
        location_source = request.form.get("location_source", "manual_input")
        
        # ========== UPDATE LOCATION TRACKER ==========
        # Immediately update the tracker with this location
        if location_source == "google_maps":
            address = request.form.get("address", "")
            location_tracker.update_location_from_google_maps(latitude, longitude, address)
        else:
            location_tracker.update_location_from_gps(latitude, longitude)
        
        # Get updated location from tracker
        location_result = location_tracker.get_current_location()
        location_data = location_result["location"]
        
        # ========== DETECT ISSUE ==========
        detected_issue = detect_issue(path)
        
        # ========== GENERATE COMPLAINT REPORT ==========
        description = generate_complaint(
            image_path=path,
            detected_class=detected_issue,
            confidence=0.87
        )
        
        # ========== FIND DEPARTMENT ==========
        dept_info = find_department_for_issue(detected_issue)
        department = dept_info["dept_name"] if dept_info else "General Municipal Department"
        
        # ========== GENERATE COMPLAINT ID ==========
        cid = generate_id()
        
        # ========== CREATE COMPLAINT RECORD ==========
        complaint = {
            "complaint_id": cid,
            "user": get_jwt_identity(),
            "issue_type": detected_issue,
            "description": description,
            "confidence": 0.87,
            "department": department,
            "location": location_data,
            "status": "pending",
            "priority": "medium",
            "timeline": [
                {
                    "status": "Registered",
                    "timestamp": datetime.datetime.now(),
                    "note": f"Complaint registered. Location source: {location_source}"
                }
            ],
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "image_path": path
        }
        
        # ========== STORE IN DATABASE ==========
        complaints.insert_one(complaint)
        
        return jsonify({
            "success": True,
            "complaint_id": cid,
            "message": f"Complaint registered successfully",
            "details": {
                "issue_type": detected_issue,
                "location_source": location_source,
                "ward": location_data.get("ward", {}).get("ward_name", "Unknown"),
                "zone": location_data.get("zone", {}).get("zone_name", "Unknown"),
                "assigned_department": department,
                "coordinates": f"{latitude}, {longitude}"
            }
        }), 201
    
    except Exception as e:
        return jsonify({
            "error": f"Error creating complaint: {str(e)}"
        }), 500

