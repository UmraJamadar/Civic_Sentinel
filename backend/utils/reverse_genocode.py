from geopy.geocoders import Nominatim

def get_area(lat, lng):
    geolocator = Nominatim(user_agent="civic")
    location = geolocator.reverse(f"{lat}, {lng}")
    return location.address if location else "Unknown"