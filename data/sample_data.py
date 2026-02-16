from models.health_models import CommunityHealthWorker, Patient, HealthVisit
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker()

def generate_sample_data(num_chws: int = 30, num_patients: int = 150, num_visits: int = 300):
    """Generate realistic sample data for ICT4D demonstration"""
    
    districts = ["Turkana", "Elgeyo-Marakwet", "Kajiado", "Nairobi"]
    villages = {
        "Turkana": ["Lodwar", "Kakuma", "Lokitaung"],
        "Elgeyo-Marakwet": ["Iten", "Kapsowar", "Tambach"],
        "Kajiado": ["Kajiado Town", "Ngong", "Kitengela"],
        "Nairobi": ["Kibera", "Mathare", "Kawangware"]
    }
    
    chws = []
    patients = []
    visits = []
    
    # Generate CHWs
    for i in range(num_chws):
        district = random.choice(districts)
        chw = CommunityHealthWorker(
            id=f"CHW{i:03d}",
            name=fake.name(),
            village=random.choice(villages[district]),
            district=district,
            phone=fake.phone_number(),
            is_active=random.random() > 0.1,  # 90% active
            date_registered=fake.date_time_between(start_date='-2y', end_date='now')
        )
        chws.append(chw)
    
    # Generate patients and assign to CHWs
    for i in range(num_patients):
        chw = random.choice(chws)
        patient = Patient(
            id=f"PAT{i:04d}",
            name=fake.name(),
            age=random.randint(1, 80),
            village=chw.village,
            chw_id=chw.id,
            is_pregnant=random.random() > 0.7 if random.randint(15, 45) else False,
            has_chronic_condition=random.random() > 0.8,
            last_visit_date=None
        )
        patients.append(patient)
        chw.patients_assigned.append(patient.id)
    
    # Generate visits
    for i in range(num_visits):
        patient = random.choice(patients)
        chw = next(c for c in chws if c.id == patient.chw_id)
        visit_date = fake.date_time_between(start_date='-6m', end_date='now')
        
        visit = HealthVisit(
            id=f"VIS{i:05d}",
            patient_id=patient.id,
            chw_id=chw.id,
            visit_date=visit_date,
            visit_type=random.choices(
                ["routine", "follow-up", "emergency"],
                weights=[0.6, 0.3, 0.1]
            )[0],
            notes=fake.sentence(),
            is_offline_sync=random.random() > 0.4  # 60% of visits done offline
        )
        visits.append(visit)
        
        # Update patient's last visit
        if not patient.last_visit_date or visit_date > patient.last_visit_date:
            patient.last_visit_date = visit_date
    
    return chws, patients, visits