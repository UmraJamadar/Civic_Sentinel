/**
 * Location Tracker Utility
 * Real-time user location extraction from multiple sources
 * 
 * Usage:
 * - Start GPS tracking: LocationTracker.startGPSTracking()
 * - Update from Google Maps: LocationTracker.updateFromGoogleMaps(lat, lng, address)
 * - Update from geotag: LocationTracker.updateFromGeotag(imageFile)
 * - Get current location: LocationTracker.getCurrentLocation()
 */

class LocationTracker {
  constructor(backendUrl = "http://localhost:5000") {
    this.backendUrl = backendUrl;
    this.gpsWatchId = null;
    this.isTracking = false;
    this.currentLocation = null;
    this.updateInterval = 5000; // 5 seconds
    this.listeners = [];
  }

  /**
   * Start continuous GPS tracking from device
   * Called automatically on app start
   */
  startGPSTracking() {
    if (!navigator.geolocation) {
      console.error("Geolocation API not supported");
      return false;
    }

    this.isTracking = true;

    // High accuracy + continuous updates
    this.gpsWatchId = navigator.geolocation.watchPosition(
      (position) => this._handleGPSPosition(position),
      (error) => this._handleGPSError(error),
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );

    console.log("GPS tracking started");
    return true;
  }

  /**
   * Stop GPS tracking
   */
  stopGPSTracking() {
    if (this.gpsWatchId !== null) {
      navigator.geolocation.clearWatch(this.gpsWatchId);
      this.isTracking = false;
      console.log("GPS tracking stopped");
    }
  }

  /**
   * Handle GPS position update from device
   * Sends to backend continuously
   */
  _handleGPSPosition(position) {
    const { latitude, longitude, accuracy } = position.coords;

    // Send to backend
    this._sendToBackend("/location/track/gps", {
      latitude,
      longitude,
      accuracy
    });

    // Notify listeners
    this._notifyListeners({
      source: "gps",
      latitude,
      longitude,
      accuracy,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Handle GPS errors
   */
  _handleGPSError(error) {
    let message;
    switch (error.code) {
      case error.PERMISSION_DENIED:
        message = "Location permission denied. Please enable in settings.";
        break;
      case error.POSITION_UNAVAILABLE:
        message = "Location service unavailable";
        break;
      case error.TIMEOUT:
        message = "Location request timeout";
        break;
      default:
        message = "Unknown location error";
    }
    console.warn(message);
  }

  /**
   * Update location from Google Maps selection
   * Called when user clicks on map
   */
  updateFromGoogleMaps(latitude, longitude, address = "", placeId = null) {
    // Send to backend
    this._sendToBackend("/location/track/google-maps", {
      latitude,
      longitude,
      address,
      place_id: placeId
    });

    // Notify listeners
    this._notifyListeners({
      source: "google_maps",
      latitude,
      longitude,
      address,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Update location from image geotag
   * Extract GPS from uploaded image EXIF data
   */
  async updateFromGeotag(imageFile) {
    try {
      const formData = new FormData();
      formData.append("image", imageFile);

      const response = await fetch(`${this.backendUrl}/location/track/geotag`, {
        method: "POST",
        body: formData
      });

      const result = await response.json();

      if (result.success || response.status === 200) {
        const location = result.location || {};
        this._notifyListeners({
          source: "image_geotag",
          latitude: location.coordinates?.latitude,
          longitude: location.coordinates?.longitude,
          timestamp: new Date().toISOString()
        });
        return result;
      } else {
        throw new Error(result.error || "No geotag found in image");
      }
    } catch (error) {
      console.error("Geotag extraction error:", error);
      throw error;
    }
  }

  /**
   * Get current tracked location
   */
  async getCurrentLocation() {
    try {
      const response = await fetch(`${this.backendUrl}/location/current`);
      const result = await response.json();
      
      if (result.success) {
        this.currentLocation = result.location;
      }
      
      return result;
    } catch (error) {
      console.error("Error fetching current location:", error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get location tracking history
   */
  async getLocationHistory(limit = 10) {
    try {
      const response = await fetch(
        `${this.backendUrl}/location/history?limit=${limit}`
      );
      return await response.json();
    } catch (error) {
      console.error("Error fetching history:", error);
      return { error: error.message };
    }
  }

  /**
   * Get location tracking status
   */
  async getStatus() {
    try {
      const response = await fetch(`${this.backendUrl}/location/status`);
      return await response.json();
    } catch (error) {
      console.error("Error fetching status:", error);
      return { error: error.message };
    }
  }

  /**
   * Clear location tracking
   */
  async clearLocation() {
    try {
      const response = await fetch(`${this.backendUrl}/location/clear`, {
        method: "POST"
      });
      return await response.json();
    } catch (error) {
      console.error("Error clearing location:", error);
      return { error: error.message };
    }
  }

  /**
   * Subscribe to location updates
   */
  onLocationUpdate(callback) {
    this.listeners.push(callback);
  }

  /**
   * Notify all listeners of location change
   */
  _notifyListeners(locationData) {
    this.listeners.forEach((callback) => {
      try {
        callback(locationData);
      } catch (error) {
        console.error("Error in location listener:", error);
      }
    });
  }

  /**
   * Send data to backend
   */
  async _sendToBackend(endpoint, data) {
    try {
      const response = await fetch(`${this.backendUrl}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        const error = await response.json();
        console.error(`Backend error at ${endpoint}:`, error);
      }
    } catch (error) {
      console.error(`Error sending to ${endpoint}:`, error);
    }
  }
}

// Export for use in React components
export default LocationTracker;

/**
 * USAGE IN REACT COMPONENT:
 * 
 * import LocationTracker from './LocationTracker';
 * 
 * useEffect(() => {
 *   const tracker = new LocationTracker();
 *   
 *   // Start continuous GPS tracking
 *   tracker.startGPSTracking();
 *   
 *   // Listen for location updates
 *   tracker.onLocationUpdate((location) => {
 *     console.log('Location updated:', location);
 *     setCurrentLocation(location);
 *   });
 *   
 *   return () => {
 *     tracker.stopGPSTracking();
 *   };
 * }, []);
 * 
 * // When user selects on Google Maps:
 * const handleMapClick = (lat, lng, address) => {
 *   tracker.updateFromGoogleMaps(lat, lng, address);
 * };
 * 
 * // When user uploads image:
 * const handleImageUpload = async (imageFile) => {
 *   try {
 *     const result = await tracker.updateFromGeotag(imageFile);
 *     console.log('Location extracted:', result);
 *   } catch (error) {
 *     console.error('No geotag in image');
 *   }
 * };
 */
