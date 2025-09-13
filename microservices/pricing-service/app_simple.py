from flask import Flask, jsonify, request
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "service": "pricing-service",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Health check",
            "POST /pricing/calculate - Calculate premium",
            "GET /pricing/{driver_id} - Get driver pricing"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "pricing-service",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

@app.route('/pricing/calculate', methods=['POST'])
def calculate_pricing():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    driver_id = data.get('driver_id')
    risk_score = data.get('risk_score', 50)
    base_premium = data.get('base_premium', 150.0)

    if not driver_id:
        return jsonify({"error": "Missing driver_id"}), 400

    # Calculate dynamic pricing based on risk
    pricing_result = calculate_dynamic_pricing(risk_score, base_premium)
    
    pricing_response = {
        "driver_id": driver_id,
        "base_premium": base_premium,
        "risk_score": risk_score,
        "adjusted_premium": pricing_result['adjusted_premium'],
        "pricing_tier": pricing_result['tier'],
        "discount_percentage": pricing_result['discount_pct'],
        "savings": pricing_result['savings'],
        "effective_date": pricing_result['effective_date'],
        "timestamp": datetime.datetime.now().isoformat()
    }

    return jsonify(pricing_response), 200

def calculate_dynamic_pricing(risk_score, base_premium):
    """Calculate dynamic pricing using 5-tier system"""
    
    # 5-Tier Pricing Model
    if risk_score < 25:
        tier = "EXCELLENT"
        discount_pct = 25  # 25% discount
    elif risk_score < 40:
        tier = "GOOD"
        discount_pct = 15  # 15% discount
    elif risk_score < 60:
        tier = "AVERAGE"
        discount_pct = 0   # No change
    elif risk_score < 75:
        tier = "POOR"
        discount_pct = -20 # 20% surcharge
    else:
        tier = "HIGH_RISK"
        discount_pct = -50 # 50% surcharge
    
    # Calculate adjusted premium
    adjustment_factor = 1 + (discount_pct / 100)
    adjusted_premium = round(base_premium * adjustment_factor, 2)
    savings = round(base_premium - adjusted_premium, 2)
    
    # Calculate effective date (next month)
    from datetime import datetime, timedelta
    next_month = datetime.now() + timedelta(days=30)
    effective_date = next_month.strftime("%Y-%m-01")
    
    return {
        'adjusted_premium': adjusted_premium,
        'tier': tier,
        'discount_pct': discount_pct,
        'savings': savings,
        'effective_date': effective_date
    }

@app.route('/pricing/tiers', methods=['GET'])
def get_pricing_tiers():
    """Return available pricing tiers"""
    tiers = {
        "EXCELLENT": {"risk_range": "0-25", "discount": "25%"},
        "GOOD": {"risk_range": "26-40", "discount": "15%"},
        "AVERAGE": {"risk_range": "41-60", "discount": "0%"},
        "POOR": {"risk_range": "61-75", "surcharge": "20%"},
        "HIGH_RISK": {"risk_range": "76-100", "surcharge": "50%"}
    }
    return jsonify(tiers), 200

@app.route('/pricing/<string:driver_id>', methods=['GET'])
def get_driver_pricing(driver_id: str):
    """Get current pricing for a driver"""
    import random
    
    # Simulate current pricing
    current_pricing = {
        "driver_id": driver_id,
        "current_premium": round(random.uniform(100, 250), 2),
        "current_tier": random.choice(["EXCELLENT", "GOOD", "AVERAGE", "POOR", "HIGH_RISK"]),
        "next_review_date": "2024-02-01",
        "pricing_history": [
            {"month": "2024-01", "premium": round(random.uniform(120, 200), 2)},
            {"month": "2023-12", "premium": round(random.uniform(110, 190), 2)},
            {"month": "2023-11", "premium": round(random.uniform(130, 210), 2)}
        ]
    }
    return jsonify(current_pricing), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, debug=True)

