from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
TELEMATICS_API_BASE = "http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com"
TRIP_SERVICE_URL = f"{TELEMATICS_API_BASE}/trips"
RISK_SERVICE_URL = f"{TELEMATICS_API_BASE}/risk/assess"
PRICING_SERVICE_URL = f"{TELEMATICS_API_BASE}/pricing/calculate"
DRIVER_SERVICE_URL = f"{TELEMATICS_API_BASE}/drivers"

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "telematics-web-backend",
        "timestamp": datetime.now().isoformat()
    })

# Get driver profile
@app.route('/api/drivers/<driver_id>/profile')
def get_driver_profile(driver_id):
    try:
        # In a real implementation, this would fetch from driver service
        # For demo purposes, we'll simulate a driver profile
        profile = {
            "driver_id": driver_id,
            "name": "Demo Driver",
            "email": "demo@example.com",
            "phone": "555-0123",
            "license_number": "DL987654321",
            "join_date": "2025-01-15",
            "total_trips": 47,
            "average_score": 78.5,
            "current_tier": "GOOD",
            "membership_level": "Silver",
            "estimated_savings": 245.75,
            "next_milestone": "Gold level (21.5 points to go)",
            "achievements": [
                {"name": "Safe Driver", "date": "2025-08-15"},
                {"name": "Consistent Performer", "date": "2025-07-22"},
                {"name": "Braking Expert", "date": "2025-06-30"}
            ]
        }
        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get driver trips
@app.route('/api/drivers/<driver_id>/trips')
def get_driver_trips(driver_id):
    try:
        # In a real implementation, this would fetch from trip service
        # For demo purposes, we'll simulate some trips
        trips = [
            {
                "trip_id": "trip_demo_1",
                "date": "2025-09-10",
                "distance_miles": 25.3,
                "duration_minutes": 45,
                "quality_score": 82,
                "feedback": [
                    "✅ Good effort on braking",
                    "🚫 Reduce hard stops for better score",
                    "✅ Maintain current speed habits"
                ]
            },
            {
                "trip_id": "trip_demo_2", 
                "date": "2025-09-08",
                "distance_miles": 18.7,
                "duration_minutes": 32,
                "quality_score": 75,
                "feedback": [
                    "✅ Smooth acceleration noted",
                    "🚫 Watch phone usage while driving",
                    "✅ Good overall driving behavior"
                ]
            },
            {
                "trip_id": "trip_demo_3",
                "date": "2025-09-05",
                "distance_miles": 32.1,
                "duration_minutes": 58,
                "quality_score": 88,
                "feedback": [
                    "🏆 Excellent driving performance!",
                    "✅ Consistent safe habits demonstrated",
                    "✅ Keep up the great work"
                ]
            }
        ]
        return jsonify(trips)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get driver risk assessment
@app.route('/api/drivers/<driver_id>/risk')
def get_driver_risk(driver_id):
    try:
        # In a real implementation, this would fetch from risk service
        # For demo purposes, we'll simulate a risk assessment
        risk = {
            "driver_id": driver_id,
            "risk_score": 22.5,
            "risk_category": "EXCELLENT",
            "factors": [
                "Consistent safe driving habits",
                "Low incidence of harsh events",
                "Good speed management"
            ],
            "contextual_factors": {
                "weather_condition": "clear",
                "temperature_f": 72,
                "visibility_mi": 10.0,
                "precipitation_inches": 0
            },
            "improvement_areas": [
                "Reduce hard braking incidents",
                "Minimize phone usage while driving"
            ],
            "strengths": [
                "Smooth acceleration",
                "Good speed management",
                "Consistent trip patterns"
            ]
        }
        return jsonify(risk)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get driver pricing
@app.route('/api/drivers/<driver_id>/pricing')
def get_driver_pricing(driver_id):
    try:
        # In a real implementation, this would fetch from pricing service
        # For demo purposes, we'll simulate pricing
        pricing = {
            "driver_id": driver_id,
            "base_premium": 150.0,
            "risk_score": 22.5,
            "adjusted_premium": 112.5,
            "pricing_tier": "EXCELLENT",
            "discount_percentage": 25,
            "savings": 37.5,
            "effective_date": "2025-10-01",
            "tier_benefits": [
                "25% premium discount",
                "Priority customer support",
                "Annual driving report"
            ]
        }
        return jsonify(pricing)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Create new trip
@app.route('/api/trips', methods=['POST'])
def create_trip():
    try:
        data = request.get_json()
        driver_id = data.get('driver_id')
        trip_data = data.get('trip_data')
        
        if not driver_id or not trip_data:
            return jsonify({"error": "Missing driver_id or trip_data"}), 400
            
        # Forward to actual trip service
        response = requests.post(
            TRIP_SERVICE_URL,
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Assess risk
@app.route('/api/risk/assess', methods=['POST'])
def assess_risk():
    try:
        data = request.get_json()
        driver_id = data.get('driver_id')
        
        if not driver_id:
            return jsonify({"error": "Missing driver_id"}), 400
            
        # Forward to actual risk service
        response = requests.post(
            RISK_SERVICE_URL,
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Calculate pricing
@app.route('/api/pricing/calculate', methods=['POST'])
def calculate_pricing():
    try:
        data = request.get_json()
        driver_id = data.get('driver_id')
        risk_score = data.get('risk_score')
        base_premium = data.get('base_premium', 150.0)
        
        if not driver_id or risk_score is None:
            return jsonify({"error": "Missing driver_id or risk_score"}), 400
            
        # Forward to actual pricing service
        response = requests.post(
            PRICING_SERVICE_URL,
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get dashboard summary
@app.route('/api/dashboard/summary')
def get_dashboard_summary():
    try:
        summary = {
            "total_trips": 1247,
            "active_drivers": 892,
            "avg_risk_score": 64.2,
            "total_savings": 24830.00,
            "recent_activity": [
                {"driver": "John D.", "action": "Completed trip", "score": 92, "time": "2 mins ago"},
                {"driver": "Sarah M.", "action": "Improved tier", "score": "GOOD → EXCELLENT", "time": "5 mins ago"},
                {"driver": "Mike R.", "action": "Saved money", "score": "$45", "time": "12 mins ago"}
            ]
        }
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)