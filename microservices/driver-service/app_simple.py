from flask import Flask, jsonify, request
import datetime
import uuid

app = Flask(__name__)

# In-memory store for demonstration
drivers_db = {}

@app.route('/')
def index():
    return jsonify({
        "service": "driver-service",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Health check",
            "POST /drivers - Create driver",
            "GET /drivers/{id} - Get driver",
            "PUT /drivers/{id} - Update driver",
            "GET /drivers - List all drivers"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "driver-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

@app.route('/drivers', methods=['POST'])
def create_driver():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    license_number = data.get('license_number')

    if not all([name, email, phone, license_number]):
        return jsonify({"error": "Missing required fields: name, email, phone, license_number"}), 400

    # Generate driver ID
    driver_id = str(uuid.uuid4())
    
    # Create driver record
    driver_record = {
        "id": driver_id,
        "name": name,
        "email": email,
        "phone": phone,
        "license_number": license_number,
        "status": "active",
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat()
    }
    
    drivers_db[driver_id] = driver_record

    return jsonify({
        "message": "Driver created successfully",
        "driver_id": driver_id,
        "driver": driver_record
    }), 201

@app.route('/drivers/<string:driver_id>', methods=['GET'])
def get_driver(driver_id: str):
    driver = drivers_db.get(driver_id)
    if driver:
        return jsonify(driver), 200
    return jsonify({"error": "Driver not found"}), 404

@app.route('/drivers/<string:driver_id>', methods=['PUT'])
def update_driver(driver_id: str):
    driver = drivers_db.get(driver_id)
    if not driver:
        return jsonify({"error": "Driver not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Update allowed fields
    updateable_fields = ['name', 'email', 'phone', 'license_number', 'status']
    for field in updateable_fields:
        if field in data:
            driver[field] = data[field]
    
    driver['updated_at'] = datetime.datetime.now().isoformat()
    drivers_db[driver_id] = driver

    return jsonify({
        "message": "Driver updated successfully",
        "driver": driver
    }), 200

@app.route('/drivers', methods=['GET'])
def list_drivers():
    drivers_list = list(drivers_db.values())
    return jsonify({
        "total_drivers": len(drivers_list),
        "drivers": drivers_list
    }), 200

@app.route('/drivers/<string:driver_id>/profile', methods=['GET'])
def get_driver_profile(driver_id: str):
    driver = drivers_db.get(driver_id)
    if not driver:
        return jsonify({"error": "Driver not found"}), 404
    
    # Enhanced profile with additional info
    import random
    profile = dict(driver)
    profile.update({
        "total_trips": random.randint(10, 500),
        "total_miles": round(random.uniform(1000, 50000), 1),
        "average_risk_score": round(random.uniform(20, 80), 1),
        "current_tier": random.choice(["EXCELLENT", "GOOD", "AVERAGE", "POOR", "HIGH_RISK"]),
        "member_since": driver['created_at'][:10]  # Just the date part
    })
    
    return jsonify(profile), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=True)

