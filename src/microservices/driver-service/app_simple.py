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
    
    # Enhanced profile with personal driving management features
    import random
    
    # Simulate getting trip data from trip service (in real implementation, this would be an API call)
    total_trips = random.randint(5, 100)
    avg_score = round(random.uniform(30, 90), 1)
    
    # Personal Driving Management Features
    insights = generate_driving_insights(total_trips, avg_score)
    
    profile = dict(driver)
    profile.update({
        "total_trips": total_trips,
        "total_miles": round(random.uniform(500, 25000), 1),
        "average_risk_score": avg_score,
        "current_tier": "EXCELLENT" if avg_score < 30 else "GOOD" if avg_score < 50 else "AVERAGE" if avg_score < 70 else "POOR" if avg_score < 85 else "HIGH_RISK",
        "member_since": driver['created_at'][:10],  # Just the date part
        "driving_insights": insights,  # NEW: Personal driving insights
        "membership_level": "Gold" if avg_score < 40 else "Silver" if avg_score < 70 else "Bronze",
        "next_milestone": f"{'Silver' if avg_score >= 70 else 'Gold' if avg_score >= 40 else 'Platinum'} level ({round(max(0, (40 if avg_score >= 70 else 70 if avg_score >= 40 else 90) - avg_score), 1)} points to go)",
        "estimated_premium_savings": f"${round(avg_score * 0.75, 2)}/year"
    })
    
    return jsonify(profile), 200

def generate_driving_insights(total_trips, avg_score):
    """Generate personalized driving insights - Personal Driving Management"""
    if total_trips == 0:
        return {
            "total_trips": 0,
            "average_score": 0,
            "improvement_areas": ["Start taking trips to build your driving profile"],
            "strengths": [],
            "personalized_recommendations": ["Complete your first trip to get personalized insights"],
            "driving_trend": "new_driver"
        }
    
    insights = {
        "total_trips": total_trips,
        "average_score": avg_score,
        "driving_trend": "improving" if avg_score < 50 else "stable" if avg_score < 70 else "needs_attention"
    }
    
    # Identify improvement areas
    improvement_areas = []
    strengths = []
    
    if avg_score > 80:
        improvement_areas.extend(["Hard braking", "Rapid acceleration", "Speed management"])
    elif avg_score > 60:
        improvement_areas.append("Consistency in safe driving habits")
    else:
        strengths.append("Consistent safe driving behavior")
    
    # Personalized recommendations
    recommendations = []
    if avg_score > 70:
        recommendations.append("Focus on smooth acceleration and braking techniques")
    elif avg_score > 40:
        recommendations.append("Maintain your good habits and strive for excellence")
    else:
        recommendations.append("You're an elite driver! Share your safe driving tips with others")
    
    insights["improvement_areas"] = improvement_areas[:3]
    insights["strengths"] = strengths
    insights["personalized_recommendations"] = recommendations
    
    return insights

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=True)

