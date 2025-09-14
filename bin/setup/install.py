#!/usr/bin/env python3
"""
Telematics Auto Insurance Setup Script
Quick setup for the entire telematics solution
"""

import os
import sys
import subprocess
import platform

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 Telematics Auto Insurance Solution Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print(f"✅ Python {sys.version} detected")
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Generate synthetic data
    if not run_command("python bin/training/generate_synthetic_drivers.py", "Generating synthetic driver data"):
        return False
    
    # Train models
    if not run_command("python bin/training/train_risk_models.py", "Training risk scoring models"):
        return False
    
    # Test system
    if not run_command("python bin/evaluation/test_real_services.py", "Testing system components"):
        print("⚠️  Some tests failed, but setup continues...")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start services: python src/api_gateway/gateway_complete.py")
    print("2. Open dashboard: http://localhost:5000")
    print("3. Run evaluation: python bin/evaluation/evaluate_models.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
