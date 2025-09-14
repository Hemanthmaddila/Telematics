# Telematics Web Application

This is a complete web application for the telematics insurance system.

## Project Structure

```
telematics-web/
├── backend/
│   ├── app.py              # Flask backend API
│   ├── requirements.txt    # Python dependencies
│   └── config.py           # Configuration
├── frontend/
│   ├── index.html          # Main dashboard
│   ├── driver.html         # Driver profile page
│   ├── trips.html          # Trips history page
│   ├── pricing.html        # Pricing calculator page
│   ├── css/
│   │   └── styles.css      # Styling
│   ├── js/
│   │   ├── main.js         # Main JavaScript
│   │   └── api.js          # API client
│   └── assets/
│       └── logo.png        # Logo image
└── README.md
```

## Features

1. **Driver Dashboard** - Shows driving scores and premium changes
2. **Trip History** - Lists all trips with feedback
3. **Risk Assessment** - Real-time risk scoring
4. **Pricing Calculator** - Shows premium discounts
5. **Profile Management** - Driver profile and settings
6. **Real-time Updates** - WebSocket for live data

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js (optional, for development)
- Docker (optional, for containerization)

### Installation

1. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure API Endpoints**
Edit `config.py` to set the telematics API endpoints:

```python
TELEMATICS_API_BASE = "http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com"
TRIP_SERVICE_URL = f"{TELEMATICS_API_BASE}/trips"
RISK_SERVICE_URL = f"{TELEMATICS_API_BASE}/risk"
PRICING_SERVICE_URL = f"{TELEMATICS_API_BASE}/pricing"
DRIVER_SERVICE_URL = f"{TELEMATICS_API_BASE}/drivers"
```

3. **Run Backend Server**
```bash
python app.py
```

The backend will be available at `http://localhost:5000`

4. **Access Frontend**
Open `frontend/index.html` in your browser or serve it with:
```bash
cd frontend
python -m http.server 8080
```

Then visit `http://localhost:8080`

## API Endpoints

### Backend Routes

- `GET /api/health` - Health check
- `GET /api/drivers/:driver_id/profile` - Get driver profile
- `GET /api/drivers/:driver_id/trips` - Get driver trips
- `GET /api/drivers/:driver_id/risk` - Get driver risk assessment
- `GET /api/drivers/:driver_id/pricing` - Get driver pricing
- `POST /api/trips` - Create new trip
- `POST /api/risk/assess` - Assess risk
- `POST /api/pricing/calculate` - Calculate pricing

### Telematics Service Routes

- Trip Service: `http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com/trips`
- Risk Service: `http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com/risk/assess`
- Pricing Service: `http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com/pricing/calculate`
- Driver Service: `http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com/drivers`

## Development

### Backend Development

1. **Run with Debug Mode**
```bash
export FLASK_ENV=development
python app.py
```

2. **Run Tests**
```bash
python -m pytest tests/
```

### Frontend Development

1. **Live Reload Development Server**
```bash
cd frontend
npx live-server --port=8080
```

## Deployment

### Docker Deployment

1. **Build Backend Image**
```bash
cd backend
docker build -t telematics-backend .
```

2. **Run Backend Container**
```bash
docker run -p 5000:5000 telematics-backend
```

3. **Serve Frontend**
The frontend can be served with any static file server or CDN.

## Security

- All API calls use HTTPS in production
- CORS is enabled for frontend-backend communication
- Rate limiting prevents abuse
- Input validation prevents injection attacks

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a pull request

## License

This project is licensed under the MIT License.

## Contact

For support, contact the development team.