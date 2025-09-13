"""Driver persona definitions for realistic behavior simulation."""

import random
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict, Any, List
from ..data.schemas import DataSource


class PersonaType(Enum):
    """Different types of driver personas for simulation."""
    SAFE_DRIVER = "safe_driver"
    AVERAGE_DRIVER = "average_driver" 
    RISKY_DRIVER = "risky_driver"


@dataclass
class BehaviorProfile:
    """Defines the behavioral characteristics of a driver persona."""
    # Event rates per 100 miles
    hard_brake_rate_range: Tuple[float, float]
    rapid_accel_rate_range: Tuple[float, float]
    harsh_corner_rate_range: Tuple[float, float]
    speeding_rate_range: Tuple[float, float]
    
    # Phone usage percentages
    phone_usage_pct_range: Tuple[float, float]
    
    # Driving patterns
    avg_speed_multiplier_range: Tuple[float, float]  # Multiplier of speed limit
    jerk_rate_multiplier_range: Tuple[float, float]  # Higher = less smooth
    
    # Risk exposure preferences
    night_driving_pct_range: Tuple[float, float]
    bad_weather_avoidance: float  # 0.0 = never avoid, 1.0 = always avoid


class DriverPersona:
    """Represents a specific driver with consistent behavioral patterns."""
    
    def __init__(self, persona_type: PersonaType, driver_id: str):
        """
        Initialize a driver persona with behavioral characteristics.
        
        Args:
            persona_type: The type of driver (safe, average, risky)
            driver_id: Unique identifier for this driver
        """
        self.persona_type = persona_type
        self.driver_id = driver_id
        self.behavior_profile = self._get_behavior_profile(persona_type)
        
        # Generate specific values for this driver within persona ranges
        self._generate_specific_behaviors()
        
        # Generate driver demographics
        self._generate_demographics()
        
    def _get_behavior_profile(self, persona_type: PersonaType) -> BehaviorProfile:
        """Get the behavior profile template for a persona type."""
        profiles = {
            PersonaType.SAFE_DRIVER: BehaviorProfile(
                hard_brake_rate_range=(0.1, 0.5),
                rapid_accel_rate_range=(0.0, 0.3),
                harsh_corner_rate_range=(0.0, 0.2),
                speeding_rate_range=(0.0, 0.2),
                phone_usage_pct_range=(0.0, 0.05),
                avg_speed_multiplier_range=(0.85, 1.0),
                jerk_rate_multiplier_range=(0.5, 0.8),
                night_driving_pct_range=(0.05, 0.15),
                bad_weather_avoidance=0.8
            ),
            PersonaType.AVERAGE_DRIVER: BehaviorProfile(
                hard_brake_rate_range=(0.5, 2.0),
                rapid_accel_rate_range=(0.3, 1.5),
                harsh_corner_rate_range=(0.2, 1.0),
                speeding_rate_range=(0.2, 1.0),
                phone_usage_pct_range=(0.05, 0.15),
                avg_speed_multiplier_range=(0.95, 1.1),
                jerk_rate_multiplier_range=(0.8, 1.2),
                night_driving_pct_range=(0.15, 0.25),
                bad_weather_avoidance=0.5
            ),
            PersonaType.RISKY_DRIVER: BehaviorProfile(
                hard_brake_rate_range=(2.0, 8.0),
                rapid_accel_rate_range=(1.5, 6.0),
                harsh_corner_rate_range=(1.0, 4.0),
                speeding_rate_range=(1.0, 5.0),
                phone_usage_pct_range=(0.15, 0.40),
                avg_speed_multiplier_range=(1.1, 1.3),
                jerk_rate_multiplier_range=(1.2, 2.0),
                night_driving_pct_range=(0.25, 0.45),
                bad_weather_avoidance=0.2
            )
        }
        return profiles[persona_type]
    
    def _generate_specific_behaviors(self):
        """Generate specific behavioral values for this driver."""
        profile = self.behavior_profile
        
        # Generate event rates
        self.hard_brake_rate = random.uniform(*profile.hard_brake_rate_range)
        self.rapid_accel_rate = random.uniform(*profile.rapid_accel_rate_range)
        self.harsh_corner_rate = random.uniform(*profile.harsh_corner_rate_range)
        self.speeding_rate = random.uniform(*profile.speeding_rate_range)
        
        # Generate phone usage
        self.phone_usage_pct = random.uniform(*profile.phone_usage_pct_range)
        
        # Generate driving patterns
        self.avg_speed_multiplier = random.uniform(*profile.avg_speed_multiplier_range)
        self.jerk_rate_multiplier = random.uniform(*profile.jerk_rate_multiplier_range)
        
        # Generate exposure patterns
        self.night_driving_pct = random.uniform(*profile.night_driving_pct_range)
        self.bad_weather_avoidance = profile.bad_weather_avoidance
        
        # Add some individual variation (±10% random factor)
        variation_factor = random.uniform(0.9, 1.1)
        self.hard_brake_rate *= variation_factor
        self.rapid_accel_rate *= variation_factor
        self.harsh_corner_rate *= variation_factor
        self.speeding_rate *= variation_factor
    
    def _generate_demographics(self):
        """Generate realistic demographic information."""
        # Age distribution based on persona
        age_ranges = {
            PersonaType.SAFE_DRIVER: (30, 65),      # More mature drivers
            PersonaType.AVERAGE_DRIVER: (25, 55),   # Broad age range
            PersonaType.RISKY_DRIVER: (18, 35)      # Younger drivers
        }
        
        age_range = age_ranges[self.persona_type]
        self.age = random.randint(*age_range)
        
        # Years licensed (minimum 1 year, realistic based on age)
        min_licensed_years = max(1, self.age - 17)
        max_licensed_years = self.age - 16
        self.years_licensed = random.randint(1, min(min_licensed_years, max_licensed_years))
        
        # Vehicle age (newer for safe drivers, older for risky)
        vehicle_age_ranges = {
            PersonaType.SAFE_DRIVER: (1, 8),
            PersonaType.AVERAGE_DRIVER: (2, 12),
            PersonaType.RISKY_DRIVER: (3, 15)
        }
        self.vehicle_age = random.randint(*vehicle_age_ranges[self.persona_type])
        
        # Prior accidents (correlated with risk)
        accident_probabilities = {
            PersonaType.SAFE_DRIVER: 0.05,
            PersonaType.AVERAGE_DRIVER: 0.15,
            PersonaType.RISKY_DRIVER: 0.35
        }
        
        accident_prob = accident_probabilities[self.persona_type]
        self.prior_at_fault_accidents = 0
        
        # Simulate multiple chances for accidents
        for _ in range(self.years_licensed):
            if random.random() < accident_prob:
                self.prior_at_fault_accidents += 1
                accident_prob *= 0.8  # Each accident slightly reduces future probability
        
        # Data source (50/50 split between phone-only and phone+device)
        self.data_source = random.choice([DataSource.PHONE_ONLY, DataSource.PHONE_PLUS_DEVICE])
    
    def calculate_claim_probability(self) -> float:
        """
        Calculate the probability of this driver having a claim.
        This creates the ground truth relationship between behavior and risk.
        """
        # Base probability
        base_probabilities = {
            PersonaType.SAFE_DRIVER: 0.02,      # 2% annual claim rate
            PersonaType.AVERAGE_DRIVER: 0.08,   # 8% annual claim rate  
            PersonaType.RISKY_DRIVER: 0.20      # 20% annual claim rate
        }
        
        base_prob = base_probabilities[self.persona_type]
        
        # Adjustments based on specific behaviors
        # Each risky behavior increases claim probability
        behavior_multiplier = 1.0
        behavior_multiplier += (self.hard_brake_rate / 100) * 0.05
        behavior_multiplier += (self.speeding_rate / 100) * 0.03
        behavior_multiplier += (self.phone_usage_pct) * 0.15
        behavior_multiplier += max(0, self.avg_speed_multiplier - 1.0) * 0.10
        
        # Demographic adjustments
        if self.age < 25:
            behavior_multiplier *= 1.3
        elif self.age > 55:
            behavior_multiplier *= 0.8
            
        if self.prior_at_fault_accidents > 0:
            behavior_multiplier *= (1.0 + self.prior_at_fault_accidents * 0.2)
        
        # Final probability (capped at 50%)
        final_prob = min(0.5, base_prob * behavior_multiplier)
        return final_prob
    
    def get_trip_parameters(self) -> Dict[str, Any]:
        """Get parameters for generating trips for this driver."""
        return {
            'avg_speed_multiplier': self.avg_speed_multiplier,
            'jerk_rate_multiplier': self.jerk_rate_multiplier,
            'hard_brake_rate': self.hard_brake_rate,
            'rapid_accel_rate': self.rapid_accel_rate,
            'harsh_corner_rate': self.harsh_corner_rate,
            'speeding_rate': self.speeding_rate,
            'phone_usage_pct': self.phone_usage_pct,
            'night_driving_pct': self.night_driving_pct,
            'bad_weather_avoidance': self.bad_weather_avoidance
        }
    
    def __repr__(self) -> str:
        return (f"DriverPersona(id={self.driver_id}, type={self.persona_type.value}, "
                f"age={self.age}, claim_prob={self.calculate_claim_probability():.3f})")


def create_driver_population(num_drivers: int, persona_distribution: Dict[PersonaType, float] = None) -> List[DriverPersona]:
    """
    Create a population of drivers with specified persona distribution.
    
    Args:
        num_drivers: Total number of drivers to create
        persona_distribution: Dictionary mapping persona types to probabilities.
                             Defaults to 60% safe, 30% average, 10% risky.
    
    Returns:
        List of DriverPersona objects
    """
    if persona_distribution is None:
        persona_distribution = {
            PersonaType.SAFE_DRIVER: 0.6,
            PersonaType.AVERAGE_DRIVER: 0.3,
            PersonaType.RISKY_DRIVER: 0.1
        }
    
    # Validate distribution sums to 1.0
    total_prob = sum(persona_distribution.values())
    if abs(total_prob - 1.0) > 0.001:
        raise ValueError(f"Persona distribution must sum to 1.0, got {total_prob}")
    
    drivers = []
    for i in range(num_drivers):
        # Select persona type based on distribution
        rand_val = random.random()
        cumulative_prob = 0.0
        
        selected_persona = PersonaType.SAFE_DRIVER  # Default
        for persona_type, prob in persona_distribution.items():
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                selected_persona = persona_type
                break
        
        driver_id = f"driver_{i+1:06d}"
        driver = DriverPersona(selected_persona, driver_id)
        drivers.append(driver)
    
    return drivers
