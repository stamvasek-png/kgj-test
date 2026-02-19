"""
Konfigurace lokalit pro KGJ Dispatch
Běhounkova a Rabasova
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
    heat_purchase_cost: float
    min_up: int
    min_down: int
    
    # Display info
    color: str = "#F0A500"
    icon: str = "🏭"
    
    @property
    def eboiler_max_heat(self):
        """Max heat output from e-boiler."""
        return self.eboiler_max_electric_input * self.eboiler_eff
    
    @property
    def total_heat_capacity(self):
        """Total aggregate heat production capacity (MWh)."""
        return self.kgj_heat_output + self.boiler_max_heat + self.eboiler_max_heat
    
    @property
    def total_ee_capacity(self):
        """Total electricity generation capacity (MWh)."""
        return self.kgj_el_output
    
    @property
    def total_gas_consumption(self):
        """Total gas consumption when KGJ at full load (MWh)."""
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
        
        # Large KGJ — aki11.xlsx parameters
        kgj_el_output=0.999,
        kgj_heat_output=1.09,
        kgj_gas_input=1.09/0.46,  # ~2.37 MWh (derived from efficiency 0.46)
        kgj_service=12.0,
        kgj_min_load=0.55,
        
        boiler_eff=0.95,
        boiler_max_heat=3.91,
        
        eboiler_eff=0.98,
        eboiler_max_electric_input=0.60564/0.98,  # ~0.618 MWh
        
        ee_dist_cost=33.0,
        heat_min_cover=0.99,
        heat_purchase_cost=0.0,  # No heat purchase
        min_up=4,
        min_down=4,
    ),
    
    "rabasova": LocationConfig(
        name="rabasova",
        display_name="Rabasova",
        short_name="RAB",
        icon="🏢",
        color="#00D4AA",
        
        # Small KGJ + heat purchase — aki12.xlsx parameters
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
        heat_purchase_cost=152.51,
        min_up=4,
        min_down=4,
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
