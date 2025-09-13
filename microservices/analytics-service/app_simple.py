from flask import Flask, jsonify, request
import datetime
import random

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "service": "analytics-service",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Health check",
            "GET /analytics/dashboard - Main dashboard",
            "POST /analytics/monthly - Monthly aggregation",
            "GET /analytics/trends - Risk trends"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "analytics-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

@app.route('/analytics/dashboard', methods=['GET'])
def get_dashboard():
    """Main analytics dashboard"""
    
    # Simulate real analytics data
    dashboard_data = {
        "overview": {
            "total_drivers": random.randint(1200, 1300),
            "total_trips": random.randint(45000, 46000),
            "avg_risk_score": round(random.uniform(40, 45), 1),
            "monthly_premium_total": round(random.uniform(180000, 220000), 2)
        },
        "risk_distribution": {
            "EXCELLENT": random.randint(200, 250),
            "GOOD": random.randint(300, 350),
            "AVERAGE": random.randint(400, 450),
            "POOR": random.randint(200, 250),
            "HIGH_RISK": random.randint(50, 100)
        },
        "monthly_trends": generate_monthly_trends(),
        "top_risk_factors": [
            {"factor": "Hard braking", "incidents": random.randint(800, 1200)},
            {"factor": "Speeding", "incidents": random.randint(600, 900)},
            {"factor": "Phone usage", "incidents": random.randint(400, 700)},
            {"factor": "Rapid acceleration", "incidents": random.randint(300, 500)}
        ],
        "pricing_impact": {
            "total_savings_distributed": round(random.uniform(15000, 25000), 2),
            "total_surcharges_applied": round(random.uniform(8000, 12000), 2),
            "net_pricing_adjustment": round(random.uniform(3000, 13000), 2)
        },
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    return jsonify(dashboard_data), 200

def generate_monthly_trends():
    """Generate monthly trend data"""
    months = ["2023-08", "2023-09", "2023-10", "2023-11", "2023-12", "2024-01"]
    trends = []
    
    base_risk = 45
    base_trips = 6000
    
    for i, month in enumerate(months):
        # Simulate improving trends over time
        risk_trend = base_risk - (i * 1.2) + random.uniform(-2, 2)
        trips_trend = base_trips + (i * 500) + random.randint(-200, 200)
        
        trends.append({
            "month": month,
            "avg_risk_score": round(risk_trend, 1),
            "total_trips": int(trips_trend),
            "premium_collected": round(random.uniform(25000, 35000), 2)
        })
    
    return trends

@app.route('/analytics/monthly', methods=['POST'])
def calculate_monthly_aggregation():
    """Calculate monthly risk aggregation for a driver"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    driver_id = data.get('driver_id')
    month = data.get('month', datetime.datetime.now().strftime("%Y-%m"))

    if not driver_id:
        return jsonify({"error": "Missing driver_id"}), 400

    # Simulate monthly aggregation calculation
    monthly_result = simulate_monthly_aggregation(driver_id, month)
    
    return jsonify(monthly_result), 200

def simulate_monthly_aggregation(driver_id, month):
    """Simulate monthly risk score aggregation"""
    
    # Simulate trip data for the month
    num_trips = random.randint(15, 35)
    trip_scores = []
    trip_weights = []
    
    for _ in range(num_trips):
        score = random.uniform(20, 80)
        weight = random.uniform(0.5, 3.0)  # Based on distance/duration
        trip_scores.append(score)
        trip_weights.append(weight)
    
    # Calculate weighted average
    total_weighted_score = sum(score * weight for score, weight in zip(trip_scores, trip_weights))
    total_weight = sum(trip_weights)
    monthly_average = total_weighted_score / total_weight if total_weight > 0 else 50
    
    # Determine trend
    previous_average = random.uniform(35, 65)
    if monthly_average < previous_average - 3:
        trend = "improving"
    elif monthly_average > previous_average + 3:
        trend = "declining"
    else:
        trend = "stable"
    
    return {
        "driver_id": driver_id,
        "month": month,
        "total_trips": num_trips,
        "monthly_average": round(monthly_average, 2),
        "previous_month_average": round(previous_average, 2),
        "trend": trend,
        "risk_category": get_risk_category(monthly_average),
        "total_miles": round(sum(trip_weights) * 8.5, 1),  # Approximate miles
        "calculation_timestamp": datetime.datetime.now().isoformat()
    }

def get_risk_category(score):
    """Convert score to risk category"""
    if score < 30:
        return "LOW"
    elif score < 50:
        return "MODERATE"
    elif score < 70:
        return "HIGH"
    else:
        return "VERY_HIGH"

@app.route('/analytics/trends', methods=['GET'])
def get_risk_trends():
    """Get risk trend analysis"""
    
    # Simulate trend analysis
    trends = {
        "overall_trend": "improving",
        "trend_percentage": round(random.uniform(-5, -2), 1),  # Negative = improving
        "period_comparison": {
            "current_period": "2024-01",
            "previous_period": "2023-12",
            "risk_score_change": round(random.uniform(-3, -1), 1),
            "trip_volume_change": random.randint(5, 15)
        },
        "risk_factor_trends": {
            "hard_braking": {"trend": "decreasing", "change_pct": round(random.uniform(-8, -3), 1)},
            "speeding": {"trend": "stable", "change_pct": round(random.uniform(-2, 2), 1)},
            "phone_usage": {"trend": "improving", "change_pct": round(random.uniform(-6, -2), 1)},
            "aggressive_driving": {"trend": "decreasing", "change_pct": round(random.uniform(-5, -1), 1)}
        },
        "predictive_insights": [
            "Risk scores trending downward - expect 5% reduction in claims",
            "Phone usage incidents decreasing due to new alerts",
            "Young drivers (18-25) showing most improvement",
            "Weekend driving risk remains elevated"
        ],
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    return jsonify(trends), 200

@app.route('/analytics/export', methods=['GET'])
def export_analytics():
    """Export analytics data"""
    export_type = request.args.get('type', 'summary')
    
    export_data = {
        "export_type": export_type,
        "generated_at": datetime.datetime.now().isoformat(),
        "data_period": "Last 6 months",
        "total_records": random.randint(10000, 50000),
        "download_url": f"/downloads/analytics_{export_type}_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
        "expires_at": (datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat()
    }
    
    return jsonify(export_data), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8086, debug=True)

