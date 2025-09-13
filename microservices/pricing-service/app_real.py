"""
Real Dynamic Pricing Engine with ML Integration

This service calculates dynamic insurance premiums based on ML-powered risk scores
with real business logic and pricing models.
"""

import os
import logging
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from typing import Dict, Any, List
import traceback

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PricingEngine:
    """Real dynamic pricing engine with ML integration"""
    
    def __init__(self):
        # Base pricing parameters
        self.base_annual_premium = 1200.0  # Base annual premium in USD
        self.min_premium = 600.0           # Minimum annual premium
        self.max_premium = 5000.0          # Maximum annual premium
        
        # Risk multiplier parameters
        self.risk_multiplier_min = 0.5     # 50% discount for lowest risk
        self.risk_multiplier_max = 3.0     # 200% surcharge for highest risk
        
        # Business rules
        self.safe_driver_discount = 0.15   # 15% discount for safe drivers
        self.young_driver_surcharge = 0.25 # 25% surcharge for drivers under 25
        self.experienced_discount = 0.10   # 10% discount for 10+ years licensed
        self.vehicle_age_surcharge = 0.05  # 5% surcharge per 5 years over 10
        self.accident_surcharge = 0.20     # 20% surcharge per at-fault accident
        
        # Telematics discount tiers
        self.telematics_discount_tiers = {
            "excellent": 0.20,  # 20% discount for excellent telematics score
            "good": 0.15,       # 15% discount for good telematics score
            "fair": 0.10,       # 10% discount for fair telematics score
            "poor": 0.0         # No discount for poor telematics score
        }
        
        # Usage-based pricing
        self.mileage_tiers = {
            "low": (0, 7500, 0.0),      # 0-7,500 miles: no surcharge
            "medium": (7501, 15000, 0.10),  # 7,501-15,000 miles: 10% surcharge
            "high": (15001, 30000, 0.25),   # 15,001-30,000 miles: 25% surcharge
            "very_high": (30001, float('inf'), 0.50)  # 30,001+ miles: 50% surcharge
        }
    
    def calculate_premium(self, driver_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate dynamic premium for a driver based on multiple factors.
        
        Args:
            driver_data: Dictionary containing driver information and risk scores
            
        Returns:
            Dictionary with premium calculation details
        """
        try:
            # Extract driver information
            driver_id = driver_data.get('driver_id', 'unknown')
            risk_score = driver_data.get('risk_score', 0.5)
            driver_age = driver_data.get('driver_age', 35)
            years_licensed = driver_data.get('years_licensed', 10)
            vehicle_age = driver_data.get('vehicle_age', 5)
            accidents = driver_data.get('prior_at_fault_accidents', 0)
            annual_mileage = driver_data.get('annual_mileage', 12000)
            telematics_score = driver_data.get('telematics_score', 0.7)
            claims_history = driver_data.get('claims_history', [])
            
            # Start with base premium
            premium = self.base_annual_premium
            
            # Apply risk-based multiplier
            risk_multiplier = self._calculate_risk_multiplier(risk_score)
            premium *= risk_multiplier
            
            # Apply driver age adjustment
            age_adjustment = self._calculate_age_adjustment(driver_age)
            premium *= (1 + age_adjustment)
            
            # Apply experience discount
            experience_discount = self._calculate_experience_discount(years_licensed)
            premium *= (1 - experience_discount)
            
            # Apply vehicle age surcharge
            vehicle_surcharge = self._calculate_vehicle_surcharge(vehicle_age)
            premium *= (1 + vehicle_surcharge)
            
            # Apply accident surcharge
            accident_surcharge = self._calculate_accident_surcharge(accidents)
            premium *= (1 + accident_surcharge)
            
            # Apply telematics discount
            telematics_discount = self._calculate_telematics_discount(telematics_score)
            premium *= (1 - telematics_discount)
            
            # Apply mileage surcharge
            mileage_surcharge = self._calculate_mileage_surcharge(annual_mileage)
            premium *= (1 + mileage_surcharge)
            
            # Apply claims history adjustment
            claims_adjustment = self._calculate_claims_adjustment(claims_history)
            premium *= (1 + claims_adjustment)
            
            # Ensure premium is within bounds
            premium = max(self.min_premium, min(self.max_premium, premium))
            
            # Calculate monthly premium
            monthly_premium = premium / 12
            
            # Generate detailed breakdown
            breakdown = {
                "base_premium": self.base_annual_premium,
                "risk_multiplier": risk_multiplier,
                "age_adjustment": age_adjustment,
                "experience_discount": experience_discount,
                "vehicle_surcharge": vehicle_surcharge,
                "accident_surcharge": accident_surcharge,
                "telematics_discount": telematics_discount,
                "mileage_surcharge": mileage_surcharge,
                "claims_adjustment": claims_adjustment,
                "final_annual_premium": round(premium, 2),
                "final_monthly_premium": round(monthly_premium, 2)
            }
            
            # Determine pricing tier
            pricing_tier = self._determine_pricing_tier(premium)
            
            return {
                "driver_id": driver_id,
                "annual_premium": round(premium, 2),
                "monthly_premium": round(monthly_premium, 2),
                "pricing_tier": pricing_tier,
                "breakdown": breakdown,
                "calculation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating premium for driver {driver_data.get('driver_id', 'unknown')}: {str(e)}")
            raise
    
    def _calculate_risk_multiplier(self, risk_score: float) -> float:
        """Calculate risk-based multiplier"""
        # Map risk score (0-1) to multiplier (0.5-3.0)
        return self.risk_multiplier_min + (risk_score * (self.risk_multiplier_max - self.risk_multiplier_min))
    
    def _calculate_age_adjustment(self, driver_age: int) -> float:
        """Calculate age-based adjustment"""
        if driver_age < 21:
            return 0.50  # 50% surcharge for very young drivers
        elif driver_age < 25:
            return 0.25  # 25% surcharge for young drivers
        elif driver_age > 65:
            return 0.15  # 15% surcharge for senior drivers
        else:
            return 0.0   # No adjustment for standard age range
    
    def _calculate_experience_discount(self, years_licensed: int) -> float:
        """Calculate experience-based discount"""
        if years_licensed >= 20:
            return self.experienced_discount * 2  # Double discount for very experienced
        elif years_licensed >= 10:
            return self.experienced_discount
        elif years_licensed < 2:
            return -0.30  # 30% surcharge for very inexperienced
        else:
            return 0.0
    
    def _calculate_vehicle_surcharge(self, vehicle_age: int) -> float:
        """Calculate vehicle age surcharge"""
        if vehicle_age > 15:
            return 0.25  # 25% surcharge for very old vehicles
        elif vehicle_age > 10:
            return 0.15  # 15% surcharge for old vehicles
        else:
            return 0.0
    
    def _calculate_accident_surcharge(self, accidents: int) -> float:
        """Calculate accident surcharge"""
        return accidents * self.accident_surcharge
    
    def _calculate_telematics_discount(self, telematics_score: float) -> float:
        """Calculate telematics-based discount"""
        if telematics_score >= 0.9:
            return self.telematics_discount_tiers["excellent"]
        elif telematics_score >= 0.7:
            return self.telematics_discount_tiers["good"]
        elif telematics_score >= 0.5:
            return self.telematics_discount_tiers["fair"]
        else:
            return self.telematics_discount_tiers["poor"]
    
    def _calculate_mileage_surcharge(self, annual_mileage: int) -> float:
        """Calculate mileage-based surcharge"""
        for tier, (min_miles, max_miles, surcharge) in self.mileage_tiers.items():
            if min_miles <= annual_mileage <= max_miles:
                return surcharge
        return 0.0
    
    def _calculate_claims_adjustment(self, claims_history: List[Dict]) -> float:
        """Calculate adjustment based on claims history"""
        if not claims_history:
            return -0.05  # 5% discount for no claims history
        
        # Count recent claims (last 3 years)
        recent_claims = [claim for claim in claims_history 
                        if datetime.fromisoformat(claim['date']) > datetime.now() - timedelta(days=3*365)]
        
        # Apply surcharge based on recent claims count
        return len(recent_claims) * 0.15  # 15% surcharge per recent claim
    
    def _determine_pricing_tier(self, premium: float) -> str:
        """Determine pricing tier based on premium amount"""
        if premium < 800:
            return "PREMIUM"
        elif premium < 1200:
            return "GOLD"
        elif premium < 1800:
            return "SILVER"
        elif premium < 2500:
            return "BRONZE"
        else:
            return "BASIC"

# Initialize pricing engine
pricing_engine = PricingEngine()

@app.route('/')
def index():
    """Health check and service information"""
    return jsonify({
        "service": "pricing-service",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": [
            "GET /health - Health check",
            "POST /pricing/calculate - Calculate premium",
            "POST /pricing/batch - Batch premium calculation",
            "GET /pricing/tiers - Get pricing tiers"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    """Service health check"""
    return jsonify({
        "status": "healthy",
        "service": "pricing-service",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/pricing/calculate', methods=['POST'])
def calculate_premium():
    """Calculate premium for a single driver"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        # Validate required fields
        required_fields = ['driver_id', 'risk_score']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Calculate premium
        result = pricing_engine.calculate_premium(data)
        
        logger.info(f"✅ Premium calculated for driver {data['driver_id']}: ${result['annual_premium']:.2f}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error calculating premium: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Failed to calculate premium: {str(e)}"
        }), 500

@app.route('/pricing/batch', methods=['POST'])
def batch_calculate_premiums():
    """Calculate premiums for multiple drivers"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        driver_data_list = data.get('drivers')
        if not driver_data_list or not isinstance(driver_data_list, list):
            return jsonify({"error": "Missing or invalid drivers array"}), 400

        results = []
        errors = []
        
        for i, driver_data in enumerate(driver_data_list):
            try:
                result = pricing_engine.calculate_premium(driver_data)
                results.append(result)
            except Exception as e:
                error_info = {
                    "driver_index": i,
                    "driver_id": driver_data.get('driver_id', 'unknown'),
                    "error": str(e)
                }
                errors.append(error_info)
                logger.error(f"Error calculating premium for driver {i}: {str(e)}")
        
        response = {
            "results": results,
            "errors": errors,
            "successful_calculations": len(results),
            "failed_calculations": len(errors),
            "total_processed": len(driver_data_list)
        }
        
        logger.info(f"✅ Batch premium calculation completed: {len(results)} successful, {len(errors)} failed")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in batch premium calculation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Failed to calculate batch premiums: {str(e)}"
        }), 500

@app.route('/pricing/tiers', methods=['GET'])
def get_pricing_tiers():
    """Get information about pricing tiers"""
    tiers = {
        "PREMIUM": {
            "description": "Lowest premium tier for safe drivers",
            "annual_range": "< $800",
            "typical_risk_score": "< 0.2",
            "discounts": ["Safe driver discount", "Experience discount", "Telematics discount"]
        },
        "GOLD": {
            "description": "Good value tier for responsible drivers",
            "annual_range": "$800 - $1,199",
            "typical_risk_score": "0.2 - 0.35",
            "discounts": ["Experience discount", "Telematics discount"]
        },
        "SILVER": {
            "description": "Standard pricing tier",
            "annual_range": "$1,200 - $1,799",
            "typical_risk_score": "0.35 - 0.55",
            "discounts": ["Telematics discount"]
        },
        "BRONZE": {
            "description": "Higher risk tier with limited discounts",
            "annual_range": "$1,800 - $2,499",
            "typical_risk_score": "0.55 - 0.75",
            "discounts": []
        },
        "BASIC": {
            "description": "Highest risk tier",
            "annual_range": "> $2,500",
            "typical_risk_score": "> 0.75",
            "discounts": []
        }
    }
    
    return jsonify({
        "pricing_tiers": tiers,
        "base_annual_premium": pricing_engine.base_annual_premium,
        "min_premium": pricing_engine.min_premium,
        "max_premium": pricing_engine.max_premium
    }), 200

@app.route('/pricing/<string:driver_id>/quote', methods=['GET'])
def get_driver_quote(driver_id: str):
    """Get a sample quote for a driver (simulated)"""
    # In a real implementation, this would query actual driver data
    # For now, we'll return simulated data
    
    # Simulate driver data
    driver_data = {
        "driver_id": driver_id,
        "risk_score": np.random.beta(2, 3),  # Most drivers have moderate risk
        "driver_age": np.random.randint(20, 70),
        "years_licensed": np.random.randint(1, 40),
        "vehicle_age": np.random.randint(0, 20),
        "prior_at_fault_accidents": np.random.poisson(0.3),
        "annual_mileage": np.random.normal(12000, 3000),
        "telematics_score": np.random.beta(3, 2),  # Most have good telematics
        "claims_history": []
    }
    
    # Calculate premium
    result = pricing_engine.calculate_premium(driver_data)
    
    return jsonify(result), 200

if __name__ == '__main__':
    logger.info("🚀 Starting Pricing Service with Real ML Integration...")
    
    # Get port from environment or default to 8083
    port = int(os.environ.get('PORT', 8083))
    
    app.run(host='0.0.0.0', port=port, debug=True)