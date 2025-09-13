"""
Telematics Insurance Risk Assessment System

A comprehensive platform for assessing driving risk using smartphone sensors,
OBD-II device data, and contextual information from mapping, weather, and traffic APIs.

This system implements a unified approach to handle both phone-only and phone+device users
through intelligent feature engineering and machine learning.
"""

__version__ = "0.1.0"
__author__ = "Telematics Team"

from .simulation import DriverPersona, PersonaType

__all__ = [
    "DriverPersona",
    "PersonaType"
]
