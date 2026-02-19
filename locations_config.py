"""
Konfigurace lokalit pro KGJ Annual Dispatch
Běhounkova a Rabasova
Fixed: plyn 35 EUR/MWh, teplo 40 EUR/MWh
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class LocationConfig:
    """Configuration for a specific location."""
    name: str
    display_name: str
    short_name: str
    
    # KGJ parameters
    kgj_el_output: float
    kgj_heat_output: float
    kgj_gas_input: float
    kgj_service: float
    kgj_min_load: float
    
    # Boiler parameters
    boiler_eff: float
    boiler_max_heat: float
    
    # E-boiler parameters
    eboiler_eff: float
    eboiler_max_electric_input: float
    
    # System parameters
    ee_dist_cost: float
    heat_min_cover: float
    min_up: int
    min_down: int
    
    # Fixed prices (EUR/MWh)
    fixed_gas_price: float = 35.0
    fixed_heat_price: float = 40.0
    
    # Display
    color: str = "#F0A500"
    icon: str = "🏭"
    
    @property
    def eboiler_max_heat(self):
        return self.eboiler_max_electric_input * self.eboiler_eff
    
    @property
    def total_heat_capacity(self):
        return self.kgj_heat_output + self.boiler_max_heat + self.eboiler_max_heat
    
    @property
    def total_ee_capacity(self):
        return self.kgj_el_output
    
    @property
    def total_gas_consumption(self):
        return self.kgj_gas_input + (self.boiler_max_heat / self.boiler_eff)


# ═══════════════════════════════════════════════
# DEFINICE LOKALIT
# ═══════════════════════════════════════════════

LOCATIONS: Dict[str, LocationConfig] = {
    
    "behounkova": LocationConfig(
        name="behounkova",
        display_name="Běhounkova",
        short_name="BEH",
        icon="🏭",
        color="#F0A500",
        
        kgj_el_output=0.999,
        kgj_heat_output=1.09,
        kgj_gas_input=1.09/0.46,
        kgj_service=12.0,
        kgj_min_load=0.55,
        
        boiler_eff=0.95,
        boiler_max_heat=3.91,
        
        eboiler_eff=0.98,
        eboiler_max_electric_input=0.60564/0.98,
        
        ee_dist_cost=33.0,
        heat_min_cover=0.99,
        min_up=4,
        min_down=4,
        
        fixed_gas_price=35.0,
        fixed_heat_price=40.0,
    ),
    
    "rabasova": LocationConfig(
        name="rabasova",
        display_name="Rabasova",
        short_name="RAB",
        icon="🏢",
        color="#00D4AA",
        
        kgj_el_output=0.45,
        kgj_heat_output=0.592,
        kgj_gas_input=1.139,
        kgj_service=7.0,
        kgj_min_load=0.55,
        
        boiler_eff=0.95,
        boiler_max_heat=0.4,
        
        eboiler_eff=0.98,
        eboiler_max_electric_input=0.414,
        
        ee_dist_cost=33.0,
        heat_min_cover=0.99,
        min_up=4,
        min_down=4,
        
        fixed_gas_price=35.0,
        fixed_heat_price=40.0,
    ),
    
}


def get_location(location_id: str) -> LocationConfig:
    """Get location config by ID."""
    if location_id not in LOCATIONS:
        raise ValueError(f"Unknown location: {location_id}")
    return LOCATIONS[location_id]


def get_location_list():
    """Get list of (id, display_name) tuples."""
    return [(loc_id, config.display_name) for loc_id, config in LOCATIONS.items()]
