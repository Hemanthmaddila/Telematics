from flask import Flask, jsonify, request
import datetime

app = Flask(__name__)

# In-memory store for demonstration
notifications_db = {}

@app.route('/')
def index():
    return jsonify({
        "service": "notification-service",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Health check",
            "POST /notifications/send - Send notification",
            "GET /notifications/{driver_id} - Get driver notifications"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "notification-service", 
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

@app.route('/notifications/send', methods=['POST'])
def send_notification():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    driver_id = data.get('driver_id')
    notification_type = data.get('type', 'general')
    title = data.get('title')
    message = data.get('message')

    if not all([driver_id, title, message]):
        return jsonify({"error": "Missing required fields: driver_id, title, message"}), 400

    # Create notification record
    notification_id = f"notif_{driver_id}_{datetime.datetime.now().timestamp()}"
    notification_record = {
        "id": notification_id,
        "driver_id": driver_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "status": "sent",
        "sent_at": datetime.datetime.now().isoformat(),
        "delivery_method": determine_delivery_method(notification_type)
    }
    
    # Store notification
    if driver_id not in notifications_db:
        notifications_db[driver_id] = []
    notifications_db[driver_id].append(notification_record)

    # Simulate sending notification
    delivery_result = simulate_notification_delivery(notification_record)

    return jsonify({
        "message": "Notification sent successfully",
        "notification_id": notification_id,
        "delivery_status": delivery_result['status'],
        "notification": notification_record
    }), 200

def determine_delivery_method(notification_type):
    """Determine the best delivery method based on notification type"""
    delivery_methods = {
        'pricing_update': ['email', 'push'],
        'safety_alert': ['push', 'sms'],
        'monthly_report': ['email'],
        'trip_feedback': ['push'],
        'general': ['push']
    }
    return delivery_methods.get(notification_type, ['push'])

def simulate_notification_delivery(notification):
    """Simulate the actual delivery of notification"""
    import random
    
    # Simulate delivery success rate
    success_rate = 0.95  # 95% success rate
    is_delivered = random.random() < success_rate
    
    delivery_time = random.uniform(0.1, 2.0)  # 0.1 to 2 seconds
    
    return {
        'status': 'delivered' if is_delivered else 'failed',
        'delivery_time_seconds': round(delivery_time, 2),
        'attempts': 1 if is_delivered else random.randint(1, 3)
    }

@app.route('/notifications/<string:driver_id>', methods=['GET'])
def get_driver_notifications(driver_id: str):
    driver_notifications = notifications_db.get(driver_id, [])
    
    # Sort by sent_at (most recent first)
    sorted_notifications = sorted(
        driver_notifications, 
        key=lambda x: x['sent_at'], 
        reverse=True
    )
    
    return jsonify({
        "driver_id": driver_id,
        "total_notifications": len(sorted_notifications),
        "notifications": sorted_notifications
    }), 200

@app.route('/notifications/stats', methods=['GET'])
def get_notification_stats():
    """Get notification delivery statistics"""
    total_notifications = sum(len(notifs) for notifs in notifications_db.values())
    total_drivers = len(notifications_db)
    
    # Calculate stats
    stats = {
        "total_notifications": total_notifications,
        "total_drivers_with_notifications": total_drivers,
        "average_notifications_per_driver": round(total_notifications / max(total_drivers, 1), 1),
        "notification_types": {
            "pricing_update": 0,
            "safety_alert": 0,
            "monthly_report": 0,
            "trip_feedback": 0,
            "general": 0
        }
    }
    
    # Count notification types
    for driver_notifs in notifications_db.values():
        for notif in driver_notifs:
            notif_type = notif.get('type', 'general')
            if notif_type in stats["notification_types"]:
                stats["notification_types"][notif_type] += 1
    
    return jsonify(stats), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, debug=True)

