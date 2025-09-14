from flask import Flask, jsonify, request
import datetime
import random

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "service": "risk-service",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Health check",
            "POST /risk/assess - Assess risk",
            "GET /risk/{driver_id} - Get driver risk profile"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "risk-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

def get_weather_context():
    """Simulate weather impact on driving risk - Smart City Integration"""
    # In real implementation, this would call a weather API
    conditions = ["clear", "rain", "snow", "fog", "windy", "clear", "clear"]  # Weighted toward clear
    condition = random.choice(conditions)
    
    return {
        "condition": condition,
        "temperature_f": random.randint(20, 95),
        "visibility_mi": round(random.uniform(0.25, 10.0), 1),
        "precipitation_inches": round(random.uniform(0, 2.0), 2) if condition in ["rain", "snow"] else 0
    }

@app.route('/risk/assess', methods=['POST'])
def assess_risk():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    driver_id = data.get('driver_id')
    trip_data = data.get('trip_data')

    if not driver_id or not trip_data:
        return jsonify({"error": "Missing driver_id or trip_data"}), 400

    # NEW: Get contextual data for Smart City Integration
    weather_context = get_weather_context()
    
    # Calculate risk score using ML-like algorithm with context
    risk_score = calculate_risk_score_with_context(trip_data, weather_context)
    risk_category = get_risk_category(risk_score)
    
    risk_assessment = {
        "driver_id": driver_id,
        "risk_score": risk_score,
        "risk_category": risk_category,
        "factors": analyze_risk_factors(trip_data),
        "contextual_factors": {  # NEW: Contextual risk factors
            "weather_condition": weather_context["condition"],
            "temperature_f": weather_context["temperature_f"],
            "visibility_mi": weather_context["visibility_mi"],
            "precipitation_inches": weather_context["precipitation_inches"],
            "contextual_risk_adjustment": "Applied" if weather_context["condition"] in ["rain", "snow", "fog"] else "None"
        },
        "timestamp": datetime.datetime.now().isoformat()
    }

    return jsonify(risk_assessment), 200

def calculate_risk_score_with_context(trip_data, weather_context=None):
    """Calculate risk score using ML-inspired algorithm with contextual data"""
    base_score = 50  # Neutral starting point
    
    # Existing behavioral factors
    hard_brakes = trip_data.get('hard_brakes', 0)
    base_score += hard_brakes * 4
    
    rapid_accels = trip_data.get('rapid_accels', 0)
    base_score += rapid_accels * 3
    
    max_speed = trip_data.get('max_speed_mph', 0)
    if max_speed > 75:
        base_score += (max_speed - 75) * 0.8
    
    phone_usage = trip_data.get('phone_usage_seconds', 0)
    base_score += phone_usage * 0.05
    
    distance = trip_data.get('distance_miles', 1)
    if distance > 10:
        base_score -= 2
    
    # NEW: Contextual risk factors from Smart City Integration
    if weather_context:
        condition = weather_context.get("condition", "clear")
        if condition == "snow":
            base_score += 12  # High risk in snow
        elif condition == "rain":
            base_score += 8   # Moderate risk in rain
        elif condition == "fog":
            base_score += 15  # Very high risk in fog
        elif condition == "windy":
            base_score += 5   # Low risk in wind
        
        visibility = weather_context.get("visibility_mi", 10.0)
        if visibility < 1.0:
            base_score += 12
        elif visibility < 3.0:
            base_score += 6
    
    # Add some ML-like variability
    ml_adjustment = random.uniform(-3, 3)
    base_score += ml_adjustment
    
    return max(0, min(100, round(base_score, 1)))

def calculate_risk_score(trip_data):
    """Calculate risk score using ML-inspired algorithm"""
    base_score = 50  # Neutral starting point
    
    # Hard braking penalty
    hard_brakes = trip_data.get('hard_brakes', 0)
    base_score += hard_brakes * 4
    
    # Rapid acceleration penalty
    rapid_accels = trip_data.get('rapid_accels', 0)
    base_score += rapid_accels * 3
    
    # Speeding penalty
    max_speed = trip_data.get('max_speed_mph', 0)
    if max_speed > 75:
        base_score += (max_speed - 75) * 0.8
    
    # Phone usage penalty
    phone_usage = trip_data.get('phone_usage_seconds', 0)
    base_score += phone_usage * 0.05
    
    # Distance adjustment (longer trips slightly safer)
    distance = trip_data.get('distance_miles', 1)
    if distance > 10:
        base_score -= 2
    
    # Add some ML-like variability
    ml_adjustment = random.uniform(-3, 3)
    base_score += ml_adjustment
    
    return max(0, min(100, round(base_score, 1)))

def get_risk_category(score):
    """Convert numeric score to risk category"""
    if score < 30:
        return "LOW"
    elif score < 50:
        return "MODERATE"
    elif score < 70:
        return "HIGH"
    else:
        return "VERY_HIGH"

def analyze_risk_factors(trip_data):
    """Analyze specific risk factors"""
    factors = []
    
    hard_brakes = trip_data.get('hard_brakes', 0)
    if hard_brakes > 3:
        factors.append(f"Excessive hard braking ({hard_brakes} events)")
    
    max_speed = trip_data.get('max_speed_mph', 0)
    if max_speed > 80:
        factors.append(f"Speeding detected ({max_speed} mph)")
    
    phone_usage = trip_data.get('phone_usage_seconds', 0)
    if phone_usage > 60:
        factors.append(f"Phone usage during trip ({phone_usage}s)")
    
    rapid_accels = trip_data.get('rapid_accels', 0)
    if rapid_accels > 2:
        factors.append(f"Aggressive acceleration ({rapid_accels} events)")
    
    if not factors:
        factors.append("No significant risk factors detected")
    
    return factors

@app.route('/risk/<string:driver_id>', methods=['GET'])
def get_driver_risk_profile(driver_id: str):
    # Simulate historical risk profile
    profile = {
        "driver_id": driver_id,
        "current_risk_score": random.randint(20, 80),
        "risk_trend": random.choice(["improving", "stable", "declining"]),
        "total_trips_analyzed": random.randint(50, 500),
        "last_assessment": datetime.datetime.now().isoformat()
    }
    return jsonify(profile), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)

