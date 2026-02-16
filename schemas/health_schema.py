import strawberry
from typing import List, Optional
from datetime import datetime, timedelta
from models.health_models import (
    CommunityHealthWorker as CHWModel,
    Patient as PatientModel,
    HealthVisit as VisitModel
)
from data.sample_data import generate_sample_data

# Sample data generator (we'll create this next)
chws, patients, visits = generate_sample_data(50, 200, 500)

@strawberry.type
class CommunityHealthWorker:
    """GraphQL type for CHW - demonstrates field-level documentation"""
    id: strawberry.ID
    name: str
    village: str
    district: str
    phone: str
    is_active: bool
    date_registered: datetime
    years_active: float
    
    @strawberry.field
    def patients(self) -> List["Patient"]:
        """Get all patients assigned to this CHW"""
        return [p for p in patients if p.chw_id == self.id]
    
    @strawberry.field
    def recent_visits(self, days: int = 30) -> List["HealthVisit"]:
        """Get visits from last N days - useful for monitoring"""
        cutoff = datetime.now() - timedelta(days=days)
        return [v for v in visits if v.chw_id == self.id and v.visit_date > cutoff]
    
    @strawberry.field
    def visit_stats(self) -> "VisitStats":
        """Return aggregated visit statistics - MEAL dashboard data"""
        chw_visits = [v for v in visits if v.chw_id == self.id]
        return VisitStats(
            total_visits=len(chw_visits),
            routine_visits=len([v for v in chw_visits if v.visit_type == "routine"]),
            emergency_visits=len([v for v in chw_visits if v.visit_type == "emergency"]),
            offline_sync_visits=len([v for v in chw_visits if v.is_offline_sync])
        )

@strawberry.type
class Patient:
    id: strawberry.ID
    name: str
    age: int
    village: str
    is_pregnant: bool
    has_chronic_condition: bool
    last_visit_date: Optional[datetime]
    
    @strawberry.field
    def assigned_chw(self) -> Optional[CommunityHealthWorker]:
        """Get the CHW assigned to this patient"""
        return next((c for c in chws if c.id == self.chw_id), None)
    
    @strawberry.field
    def visit_history(self) -> List["HealthVisit"]:
        """Get all visits for this patient"""
        return [v for v in visits if v.patient_id == self.id]

@strawberry.type
class HealthVisit:
    id: strawberry.ID
    visit_type: str
    visit_date: datetime
    notes: str
    is_offline_sync: bool
    
    @strawberry.field
    def patient(self) -> Optional[Patient]:
        return next((p for p in patients if p.id == self.patient_id), None)
    
    @strawberry.field
    def chw(self) -> Optional[CommunityHealthWorker]:
        return next((c for c in chws if c.id == self.chw_id), None)

@strawberry.type
class VisitStats:
    """Statistics type for dashboards"""
    total_visits: int
    routine_visits: int
    emergency_visits: int
    offline_sync_visits: int
    
    @strawberry.field
    def completion_rate(self) -> float:
        """Percentage of visits that were routine vs emergency"""
        if self.total_visits == 0:
            return 0.0
        return (self.routine_visits / self.total_visits) * 100

@strawberry.type
class Query:
    """Main GraphQL Query - demonstrates the 'analytical and problem-solving mindset' [citation:2]"""
    
    @strawberry.field
    def health_workers(self, 
                      district: Optional[str] = None,
                      is_active: Optional[bool] = None) -> List[CommunityHealthWorker]:
        """Filter CHWs by district and status - supports stakeholder queries"""
        result = chws
        if district:
            result = [c for c in result if c.district == district]
        if is_active is not None:
            result = [c for c in result if c.is_active == is_active]
        return result
    
    @strawberry.field
    def patients_needing_visits(self, days_threshold: int = 30) -> List[Patient]:
        """Identify patients who haven't been visited - proactive care"""
        return [p for p in patients if p.needs_visit(days_threshold)]
    
    @strawberry.field
    def district_summary(self, district: str) -> "DistrictSummary":
        """High-level district metrics for government reporting [citation:1]"""
        district_chws = [c for c in chws if c.district == district]
        district_patients = [p for p in patients if p.village in [c.village for c in district_chws]]
        district_visits = [v for v in visits if v.chw_id in [c.id for c in district_chws]]
        
        return DistrictSummary(
            district=district,
            total_chws=len(district_chws),
            total_patients=len(district_patients),
            total_visits=len(district_visits),
            active_chws=len([c for c in district_chws if c.is_active])
        )
    
    @strawberry.field
    def offline_sync_status(self) -> "OfflineSyncReport":
        """Monitor offline data collection - critical for low-bandwidth areas [citation:7]"""
        offline_visits = [v for v in visits if v.is_offline_sync]
        return OfflineSyncReport(
            total_offline_visits=len(offline_visits),
            unique_chws_offline=len(set(v.chw_id for v in offline_visits)),
            last_week_offline=len([v for v in offline_visits 
                                   if v.visit_date > datetime.now() - timedelta(days=7)])
        )

@strawberry.type
class DistrictSummary:
    """Summary type for dashboard visualizations"""
    district: str
    total_chws: int
    total_patients: int
    total_visits: int
    active_chws: int
    
    @strawberry.field
    def patient_to_chw_ratio(self) -> float:
        """Key metric for program planning"""
        if self.total_chws == 0:
            return 0.0
        return round(self.total_patients / self.total_chws, 1)

@strawberry.type
class OfflineSyncReport:
    """Report on offline data collection capabilities"""
    total_offline_visits: int
    unique_chws_offline: int
    last_week_offline: int
    
    @strawberry.field
    def offline_adoption_rate(self) -> float:
        """Measure of technology adoption by CHWs"""
        if len(visits) == 0:
            return 0.0
        return (self.total_offline_visits / len(visits)) * 100

# Create schema
schema = strawberry.Schema(query=Query)