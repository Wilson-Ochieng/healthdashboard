from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
import random

@dataclass
class CommunityHealthWorker:
    """Model representing a CHW - core to ICT4D programs"""
    id: str
    name: str
    village: str
    district: str
    phone: str
    is_active: bool = True
    date_registered: datetime = field(default_factory=datetime.now)
    patients_assigned: List[str] = field(default_factory=list)
    
    def years_active(self) -> float:
        """Calculate years of service"""
        days = (datetime.now() - self.date_registered).days
        return round(days / 365.25, 1)

@dataclass
class Patient:
    """Model representing a patient in the program"""
    id: str
    name: str
    age: int
    village: str
    chw_id: str  # Assigned Community Health Worker
    is_pregnant: bool = False
    has_chronic_condition: bool = False
    last_visit_date: Optional[datetime] = None
    
    def needs_visit(self, days_threshold: int = 30) -> bool:
        """Check if patient needs a follow-up visit"""
        if not self.last_visit_date:
            return True
        days_since = (datetime.now() - self.last_visit_date).days
        return days_since > days_threshold
        

@dataclass
class HealthVisit:
    """Model representing a health visit - key for MEAL tracking"""
    id: str
    patient_id: str
    chw_id: str
    visit_date: datetime
    visit_type: str  # "routine", "emergency", "follow-up"
    notes: str
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    is_offline_sync: bool = False  # Important for low-bandwidth scenarios
    
    @property
    def visit_summary(self) -> str:
        """Generate a summary for reports"""
        return f"{self.visit_type} visit on {self.visit_date.strftime('%Y-%m-%d')}: {self.notes[:50]}..."