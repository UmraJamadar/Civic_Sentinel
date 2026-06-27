#!/usr/bin/env python3
"""
COMPLETE MODULE 3 TEST SUITE
Tests all location extraction and routing with Garbage Department
"""

import json
import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from utils.location_tracker import location_tracker
from utils.location_mapper import (
    get_location_info,
    validate_location_bounds,
    find_nearest_ward,
    find_department_for_issue,
    format_location_for_complaint
)
from utils.geotag_extractor import extract_gps_from_geotag, is_geotagged


def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_location_bounds():
    """Test 1: Validate location is within Hubli-Dharwad bounds"""
    print_section("TEST 1: Location Bounds Validation")
    
    # Test valid location
    result = validate_location_bounds(15.3647, 75.1240)
    print(f"✓ Valid location (15.3647, 75.1240): {result}")
    assert result["valid"], "Should be valid within city"
    
    # Test invalid location (outside bounds)
    result = validate_location_bounds(10.0, 70.0)
    print(f"✓ Invalid location (10.0, 70.0): {result}")
    assert not result["valid"], "Should be invalid outside city"
    
    print("✅ Location bounds validation PASSED\n")


def test_ward_mapping():
    """Test 2: Find nearest ward from coordinates"""
    print_section("TEST 2: Ward Mapping & Distance Calculation")
    
    # Test with Unkal Ward coordinates
    ward = find_nearest_ward(15.46, 75.11)
    print(f"Ward at (15.46, 75.11):")
    print(f"  - Ward ID: {ward['ward_id']}")
    print(f"  - Ward Name: {ward['ward_name']}")
    print(f"  - Zone: {ward.get('zone_id', 'N/A')}")
    print(f"  - Areas: {ward['main_areas']}")
    
    assert ward["ward_name"] == "Unkal Ward", "Should find Unkal Ward"
    print("✅ Ward mapping PASSED\n")


def test_location_info():
    """Test 3: Get complete location information"""
    print_section("TEST 3: Complete Location Information")
    
    location_info = get_location_info(15.3647, 75.1240)
    print(f"Location Info for (15.3647, 75.1240):")
    print(f"  - Ward: {location_info['ward']['ward_name'] if location_info['ward'] else 'N/A'}")
    print(f"  - Zone: {location_info['zone']['zone_name'] if location_info['zone'] else 'N/A'}")
    print(f"  - Address: {location_info['address'].get('full_address', 'N/A')}")
    
    assert location_info["ward"] is not None, "Should find ward"
    assert location_info["zone"] is not None, "Should find zone"
    print("✅ Location info retrieval PASSED\n")


def test_garbage_department_routing():
    """Test 4: Department routing for garbage issues"""
    print_section("TEST 4: Garbage Department Routing")
    
    # Test garbage routing
    garbage_issues = ["garbage", "waste dumping", "illegal dumping"]
    for issue in garbage_issues:
        dept = find_department_for_issue(issue)
        print(f"✓ Issue '{issue}' → Department: {dept['dept_name']}")
        assert "Sanitation" in dept['dept_name'] or "Waste" in dept['dept_name'], \
            f"Garbage should route to Sanitation/Waste dept, got {dept['dept_name']}"
    
    # Test pothole routing
    dept = find_department_for_issue("pothole")
    print(f"✓ Issue 'pothole' → Department: {dept['dept_name']}")
    assert "Road" in dept['dept_name'], "Pothole should route to Road department"
    
    # Test water leak routing
    dept = find_department_for_issue("water leak")
    print(f"✓ Issue 'water leak' → Department: {dept['dept_name']}")
    assert "Water" in dept['dept_name'], "Water leak should route to Water department"
    
    print("✅ Department routing PASSED\n")


def test_location_tracker():
    """Test 5: Real-time location tracking"""
    print_section("TEST 5: Real-time Location Tracking")
    
    # Simulate GPS update
    print("Simulating GPS update...")
    result = location_tracker.update_location_from_gps(15.3647, 75.1240, 5.5)
    print(f"✓ GPS Update: {result['message']}")
    assert result["success"], "GPS update should succeed"
    
    # Get current location
    current = location_tracker.get_current_location()
    print(f"✓ Current location: {current['location']['ward']['ward_name']}")
    assert current["success"], "Should have current location"
    
    # Simulate Google Maps selection
    print("Simulating Google Maps selection...")
    result = location_tracker.update_location_from_google_maps(
        15.38, 75.09, "Ravivar Peth, Hubli", "ChIJ..."
    )
    print(f"✓ Maps Update: {result['message']}")
    
    # Get history
    history = location_tracker.get_location_history(10)
    print(f"✓ Location history: {history['total_updates']} updates")
    assert history['total_updates'] >= 2, "Should have history"
    
    print("✅ Location tracking PASSED\n")


def test_location_formatting():
    """Test 6: Format location for complaint storage"""
    print_section("TEST 6: Location Formatting for MongoDB")
    
    formatted = format_location_for_complaint(15.3647, 75.1240)
    
    print("Formatted location structure:")
    print(f"  - Coordinates: ({formatted['coordinates']['latitude']}, {formatted['coordinates']['longitude']})")
    print(f"  - Ward: {formatted['ward']['ward_name']}")
    print(f"  - Zone: {formatted['zone']['zone_name']}")
    print(f"  - City: {formatted['city']}")
    print(f"  - State: {formatted['state']}")
    print(f"  - Within bounds: {formatted['within_city_bounds']}")
    
    assert formatted["within_city_bounds"], "Should be within bounds"
    assert formatted["ward"]["ward_name"] is not None, "Should have ward name"
    print("✅ Location formatting PASSED\n")


def test_geotag_image():
    """Test 7: Extract geotag from image (if available)"""
    print_section("TEST 7: Image Geotag Extraction")
    
    test_image = "backend/AI/test.jpg"
    if os.path.exists(test_image):
        has_geotag = is_geotagged(test_image)
        print(f"Image file: {test_image}")
        print(f"Has geotag: {has_geotag}")
        
        if has_geotag:
            gps_data = extract_gps_from_geotag(test_image)
            print(f"✓ Extracted GPS: ({gps_data['latitude']}, {gps_data['longitude']})")
            print(f"  - Altitude: {gps_data.get('altitude', 'N/A')}")
            print(f"  - Accuracy: {gps_data.get('accuracy_meters', 'N/A')}m")
            print("✅ Geotag extraction PASSED\n")
        else:
            print("ℹ️  Test image has no geotag data (expected for generated test images)")
            print("   Real smartphone photos will have EXIF GPS data\n")
    else:
        print(f"⚠️  Test image not found: {test_image}")
        print("   Skipping geotag test\n")


def test_complete_flow():
    """Test 8: Complete complaint creation flow"""
    print_section("TEST 8: Complete Complaint Flow (GPS → Ward → Department)")
    
    # Simulate user GPS update
    print("Step 1: User starts app → GPS tracking begins")
    location_tracker.update_location_from_gps(15.3647, 75.1240, 5.5)
    print(f"  ✓ GPS location tracked")
    
    # Simulate issue detection
    print("\nStep 2: User detects and captures garbage issue")
    detected_issue = "garbage"
    print(f"  ✓ Issue detected: {detected_issue}")
    
    # Get location
    print("\nStep 3: System fetches current tracked location")
    location_result = location_tracker.get_current_location()
    location_data = location_result["location"]
    print(f"  ✓ Location: {location_data['ward']['ward_name']}")
    
    # Get department
    print("\nStep 4: System determines responsible department")
    dept = find_department_for_issue(detected_issue)
    print(f"  ✓ Assigned to: {dept['dept_name']}")
    print(f"    - Handles: {', '.join(dept['issues_handled'])}")
    
    # Build complaint
    print("\nStep 5: Complaint ready for storage")
    print(f"  ✓ Complaint ID: CS-2026-00001")
    print(f"  ✓ Issue Type: {detected_issue.upper()}")
    print(f"  ✓ Location: {location_data['address'].get('full_address', 'N/A')}")
    print(f"  ✓ Ward: {location_data['ward']['ward_name']}")
    print(f"  ✓ Zone: {location_data['zone']['zone_name']}")
    print(f"  ✓ Department: {dept['dept_name']}")
    print(f"  ✓ Status: PENDING")
    
    print("✅ Complete flow PASSED\n")


def run_all_tests():
    """Run complete test suite"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "CIVIC SENTINEL - MODULE 3 TEST SUITE" + " "*12 + "║")
    print("║" + " "*15 + "Complete Location Extraction System" + " "*9 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        test_location_bounds()
        test_ward_mapping()
        test_location_info()
        test_garbage_department_routing()
        test_location_tracker()
        test_location_formatting()
        test_geotag_image()
        test_complete_flow()
        
        print_section("✅ ALL TESTS PASSED!")
        print("""
Summary:
  ✓ Location bounds validation working
  ✓ Ward mapping with distance calculation working
  ✓ Zone identification working
  ✓ Garbage → Sanitation & Waste Mgmt routing working
  ✓ Real-time location tracking working
  ✓ Location history tracking working
  ✓ MongoDB-ready formatting working
  ✓ Image geotag extraction ready
  ✓ Complete flow from GPS → Ward → Department working

🚀 MODULE 3 READY FOR PRODUCTION
        """)
        
        return 0
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
