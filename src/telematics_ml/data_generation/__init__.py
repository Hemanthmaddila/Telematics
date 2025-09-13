"""Driver behavior simulation for telematics data generation."""

from .driver_personas import DriverPersona, PersonaType, create_driver_population

__all__ = [
    "DriverPersona",
    "PersonaType",
    "create_driver_population"
]
