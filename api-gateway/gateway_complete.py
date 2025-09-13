from flask import Flask, request, jsonify
import requests
import os
import datetime

app = Flask(__name__)

# Service URLs from environment variables
TRIP_SERVICE_URL = os.getenv('TRIP_SERVICE_URL', 'http://localhost:8081')
RISK_SERVICE_URL = os.getenv('RISK_SERVICE_URL', 'http://localhost:8082')
PRICING_SERVICE_URL = os.getenv('PRICING_SERVICE_URL', 'http://localhost:8083')
DRIVER_SERVICE_URL = os.getenv('DRIVER_SERVICE_URL', 'http://localhost:8084')
NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://localhost:8085')
ANALYTICS_SERVICE_URL = os.getenv('ANALYTICS_SERVICE_URL', 'http://localhost:8086')

@app.route('/')
def index():
    return jsonify({
        "service": "telematics-api-gateway",
        "version": "1.0.0",
        "description": "Complete Telematics Insurance ML Platform",
        "services": {
            "trip": f"{TRIP_SERVICE_URL}",
            "risk": f"{RISK_SERVICE_URL}",
            "pricing": f"{PRICING_SERVICE_URL}",
            "driver": f"{DRIVER_SERVICE_URL}",
            "notification": f"{NOTIFICATION_SERVICE_URL}",
            "analytics": f"{ANALYTICS_SERVICE_URL}"
        },
        "endpoints": [
            "GET /health - System health check",
            "GET /services/status - All services status",
            "POST /trips - Create trip (Trip Service)",
            "POST /risk/assess - Assess risk (Risk Service)",
            "POST /pricing/calculate - Calculate pricing (Pricing Service)",
            "POST /drivers - Create driver (Driver Service)",
            "POST /notifications/send - Send notification (Notification Service)",
            "GET /analytics/dashboard - Analytics dashboard (Analytics Service)"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "gateway": "operational",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200

@app.route('/services/status', methods=['GET'])
def services_status():
    """Check status of all microservices"""
    services = {
        "trip-service": TRIP_SERVICE_URL,
        "risk-service": RISK_SERVICE_URL,
        "pricing-service": PRICING_SERVICE_URL,
        "driver-service": DRIVER_SERVICE_URL,
        "notification-service": NOTIFICATION_SERVICE_URL,
        "analytics-service": ANALYTICS_SERVICE_URL
    }
    
    status_results = {}
    
    for service_name, service_url in services.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            if response.status_code == 200:
                status_results[service_name] = {
                    "status": "healthy",
                    "url": service_url,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                status_results[service_name] = {
                    "status": "unhealthy",
                    "url": service_url,
                    "error": f"HTTP {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            status_results[service_name] = {
                "status": "down",
                "url": service_url,
                "error": str(e)
            }
    
    # Overall system status
    healthy_services = sum(1 for s in status_results.values() if s["status"] == "healthy")
    total_services = len(status_results)
    
    overall_status = "healthy" if healthy_services == total_services else \
                    "degraded" if healthy_services > total_services // 2 else "unhealthy"
    
    return jsonify({
        "overall_status": overall_status,
        "healthy_services": f"{healthy_services}/{total_services}",
        "services": status_results,
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

# Trip Service Routes
@app.route('/trips', methods=['POST'])
def create_trip():
    return proxy_request(TRIP_SERVICE_URL, '/trips', request.method)

@app.route('/trips/<trip_id>', methods=['GET'])
def get_trip(trip_id):
    return proxy_request(TRIP_SERVICE_URL, f'/trips/{trip_id}', request.method)

@app.route('/drivers/<driver_id>/trips', methods=['GET'])
def get_driver_trips(driver_id):
    return proxy_request(TRIP_SERVICE_URL, f'/drivers/{driver_id}/trips', request.method)

# Risk Service Routes
@app.route('/risk/assess', methods=['POST'])
def assess_risk():
    return proxy_request(RISK_SERVICE_URL, '/risk/assess', request.method)

@app.route('/risk/<driver_id>', methods=['GET'])
def get_driver_risk(driver_id):
    return proxy_request(RISK_SERVICE_URL, f'/risk/{driver_id}', request.method)

# Pricing Service Routes
@app.route('/pricing/calculate', methods=['POST'])
def calculate_pricing():
    return proxy_request(PRICING_SERVICE_URL, '/pricing/calculate', request.method)

@app.route('/pricing/<driver_id>', methods=['GET'])
def get_driver_pricing(driver_id):
    return proxy_request(PRICING_SERVICE_URL, f'/pricing/{driver_id}', request.method)

@app.route('/pricing/tiers', methods=['GET'])
def get_pricing_tiers():
    return proxy_request(PRICING_SERVICE_URL, '/pricing/tiers', request.method)

# Driver Service Routes
@app.route('/drivers', methods=['POST', 'GET'])
def drivers():
    return proxy_request(DRIVER_SERVICE_URL, '/drivers', request.method)

@app.route('/drivers/<driver_id>', methods=['GET', 'PUT'])
def driver_operations(driver_id):
    return proxy_request(DRIVER_SERVICE_URL, f'/drivers/{driver_id}', request.method)

@app.route('/drivers/<driver_id>/profile', methods=['GET'])
def get_driver_profile(driver_id):
    return proxy_request(DRIVER_SERVICE_URL, f'/drivers/{driver_id}/profile', request.method)

# Notification Service Routes
@app.route('/notifications/send', methods=['POST'])
def send_notification():
    return proxy_request(NOTIFICATION_SERVICE_URL, '/notifications/send', request.method)

@app.route('/notifications/<driver_id>', methods=['GET'])
def get_driver_notifications(driver_id):
    return proxy_request(NOTIFICATION_SERVICE_URL, f'/notifications/{driver_id}', request.method)

@app.route('/notifications/stats', methods=['GET'])
def get_notification_stats():
    return proxy_request(NOTIFICATION_SERVICE_URL, '/notifications/stats', request.method)

# Analytics Service Routes
@app.route('/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    return proxy_request(ANALYTICS_SERVICE_URL, '/analytics/dashboard', request.method)

@app.route('/analytics/monthly', methods=['POST'])
def calculate_monthly_analytics():
    return proxy_request(ANALYTICS_SERVICE_URL, '/analytics/monthly', request.method)

@app.route('/analytics/trends', methods=['GET'])
def get_analytics_trends():
    return proxy_request(ANALYTICS_SERVICE_URL, '/analytics/trends', request.method)

@app.route('/analytics/export', methods=['GET'])
def export_analytics():
    return proxy_request(ANALYTICS_SERVICE_URL, '/analytics/export', request.method)

def proxy_request(service_url, path, method):
    """Proxy HTTP request to the appropriate microservice"""
    try:
        # Prepare request data
        json_data = request.get_json() if request.is_json else None
        params = request.args.to_dict()
        
        # Make request to microservice
        if method == 'GET':
            response = requests.get(f"{service_url}{path}", params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(f"{service_url}{path}", json=json_data, params=params, timeout=10)
        elif method == 'PUT':
            response = requests.put(f"{service_url}{path}", json=json_data, params=params, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(f"{service_url}{path}", params=params, timeout=10)
        else:
            return jsonify({"error": "Method not supported"}), 405
        
        # Return response from microservice
        try:
            return jsonify(response.json()), response.status_code
        except ValueError:
            # Response is not JSON
            return response.text, response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Service timeout",
            "service": service_url,
            "path": path
        }), 504
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Service unavailable",
            "service": service_url,
            "path": path
        }), 503
        
    except Exception as e:
        return jsonify({
            "error": "Internal gateway error",
            "details": str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/health", "/services/status",
            "/trips", "/risk/assess", "/pricing/calculate",
            "/drivers", "/notifications/send", "/analytics/dashboard"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred in the API Gateway"
    }), 500

if __name__ == '__main__':
    print("🚀 Starting Telematics API Gateway...")
    print(f"Trip Service: {TRIP_SERVICE_URL}")
    print(f"Risk Service: {RISK_SERVICE_URL}")
    print(f"Pricing Service: {PRICING_SERVICE_URL}")
    print(f"Driver Service: {DRIVER_SERVICE_URL}")
    print(f"Notification Service: {NOTIFICATION_SERVICE_URL}")
    print(f"Analytics Service: {ANALYTICS_SERVICE_URL}")
    
    app.run(host='0.0.0.0', port=8080, debug=True)

