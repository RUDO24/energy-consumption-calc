from dataclasses import dataclass
from typing import List
@dataclass
class Settings:
    object_name: str = ""
    max_power: float = 0.0
@dataclass
class Device:
    location: str
    type: str
    name: str
    power: float
    time_from: int
    time_to: int
@dataclass
class AppData:
    settings: Settings
    devices: List[Device]