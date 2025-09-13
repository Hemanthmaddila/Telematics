from flask import Flask, jsonify, request
import datetime

app = Flask(__name__)

# In-memory store for demonstration
trips_db = {}
drivers_db = {}

@app.route('/')
def index():
    return jsonify({
        "service": "trip-service",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Health check",
            "POST /trips - Create trip",
            "GET /trips/{id} - Get trip",
            "GET /drivers/{id}/trips - Get driver trips"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "trip-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

@app.route('/trips', methods=['POST'])
def create_trip():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    driver_id = data.get('driver_id')
    trip_data_raw = data.get('trip_data')

    if not driver_id or not trip_data_raw:
        return jsonify({"error": "Missing driver_id or trip_data"}), 400

    # Calculate quality score based on trip data
    quality_score = calculate_trip_quality(trip_data_raw)
    
    # Simulate trip creation and storage
    trip_id = f"trip_{driver_id}_{datetime.datetime.now().timestamp()}"
    trip_record = {
        "id": trip_id,
        "driver_id": driver_id,
        "trip_data": trip_data_raw,
        "quality_score": quality_score,
        "created_at": datetime.datetime.now().isoformat()
    }
    trips_db[trip_id] = trip_record
    drivers_db.setdefault(driver_id, []).append(trip_id)

    return jsonify({
        "message": "Trip created successfully", 
        "trip_id": trip_id, 
        "quality_score": quality_score,
        "trip": trip_record
    }), 201

def calculate_trip_quality(trip_data):
    """Calculate trip quality score (0-100)"""
    score = 100
    
    # Reduce score for risky behaviors
    hard_brakes = trip_data.get('hard_brakes', 0)
    score -= hard_brakes * 5
    
    rapid_accels = trip_data.get('rapid_accels', 0)
    score -= rapid_accels * 3
    
    phone_usage = trip_data.get('phone_usage_seconds', 0)
    score -= phone_usage * 0.1
    
    max_speed = trip_data.get('max_speed_mph', 0)
    if max_speed > 75:
        score -= (max_speed - 75) * 0.5
    
    return max(0, min(100, round(score, 1)))

@app.route('/trips/<string:trip_id>', methods=['GET'])
def get_trip(trip_id: str):
    trip = trips_db.get(trip_id)
    if trip:
        return jsonify(trip), 200
    return jsonify({"error": "Trip not found"}), 404

@app.route('/drivers/<string:driver_id>/trips', methods=['GET'])
def get_driver_trips(driver_id: str):
    trip_ids = drivers_db.get(driver_id, [])
    trips = [trips_db[tid] for tid in trip_ids]
    return jsonify(trips), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)

