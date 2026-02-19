from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, unset_jwt_cookies, verify_jwt_in_request
from functools import wraps
from strawberry.flask.views import GraphQLView
from schemas.health_schema import schema
from models.health_models import CommunityHealthWorker, Patient, HealthVisit
from routes.auth_routes import auth_bp, users as auth_users
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ict4d-secret-key-2026')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-2026')
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Enable in production with proper CSRF
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize JWT
jwt = JWTManager(app)
# JWT error handlers
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    """Redirect to login when no token is provided"""
    return redirect(url_for('auth.login_page', next=request.path))

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Redirect to login when token has expired"""
    return redirect(url_for('auth.login_page', next=request.path, expired=1))

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    """Redirect to login when token is invalid"""
    return redirect(url_for('auth.login_page', next=request.path))

# Register auth blueprint
app.register_blueprint(auth_bp)

# In-memory database
from data.sample_data import generate_sample_data
chws, patients, visits = generate_sample_data(30, 150, 300)

# Merge users from auth blueprint for template access
users = auth_users

# Add GraphQL endpoint
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

# ============== JWT PROTECTED ROUTES ==============
@app.route('/')
@jwt_required(optional=True)
def index():
    """Main dashboard with key ICT4D metrics"""
    # Get current user if authenticated
    from flask_jwt_extended import get_jwt_identity
    current_email = get_jwt_identity()
    current_user = users.get(current_email) if current_email else None
    
    total_chws = len(chws)
    total_patients = len(patients)
    total_visits = len(visits)
    active_chws = len([c for c in chws if c.is_active])
    visits_this_week = len([v for v in visits 
                           if v.visit_date > datetime.now() - timedelta(days=7)])
    
    # District breakdown
    districts = {}
    for chw in chws:
        if chw.district not in districts:
            districts[chw.district] = {
                'chws': 0,
                'patients': 0,
                'visits': 0
            }
        districts[chw.district]['chws'] += 1
    
    for patient in patients:
        chw = next((c for c in chws if c.id == patient.chw_id), None)
        if chw and chw.district in districts:
            districts[chw.district]['patients'] += 1
    
    for visit in visits:
        chw = next((c for c in chws if c.id == visit.chw_id), None)
        if chw and chw.district in districts:
            districts[chw.district]['visits'] += 1
    
    # Recent activities
    recent_visits = sorted(visits, key=lambda x: x.visit_date, reverse=True)[:10]
    
    return render_template('dashboard.html',
                         total_chws=total_chws,
                         total_patients=total_patients,
                         total_visits=total_visits,
                         active_chws=active_chws,
                         visits_this_week=visits_this_week,
                         districts=districts,
                         recent_visits=recent_visits)

# ============== CHW CRUD ROUTES ==============

@app.route('/chws')
def list_chws():
    """List all Community Health Workers"""
    district = request.args.get('district')
    status = request.args.get('status')
    
    filtered_chws = chws
    if district:
        filtered_chws = [c for c in filtered_chws if c.district == district]
    if status == 'active':
        filtered_chws = [c for c in filtered_chws if c.is_active]
    elif status == 'inactive':
        filtered_chws = [c for c in filtered_chws if not c.is_active]
    
    districts = sorted(set(c.district for c in chws))
    return render_template('chw_list.html', 
                         chws=filtered_chws, 
                         districts=districts,
                         selected_district=district,
                         selected_status=status)

@app.route('/chws/new', methods=['GET', 'POST'])
def create_chw():
    """Create new CHW"""
    if request.method == 'POST':
        new_id = f"CHW{len(chws)+1:03d}"
        chw = CommunityHealthWorker(
            id=new_id,
            name=request.form['name'],
            village=request.form['village'],
            district=request.form['district'],
            phone=request.form['phone'],
            is_active='is_active' in request.form
        )
        chws.append(chw)
        flash(f'CHW {chw.name} created successfully!', 'success')
        return redirect(url_for('list_chws'))
    
    districts = ["Turkana", "Elgeyo-Marakwet", "Kajiado", "Nairobi", "Marsabit", "Garissa"]
    return render_template('chw_form.html', chw=None, districts=districts)

@app.route('/chws/<chw_id>/edit', methods=['GET', 'POST'])
def edit_chw(chw_id):
    """Edit existing CHW"""
    chw = next((c for c in chws if c.id == chw_id), None)
    if not chw:
        flash('CHW not found!', 'error')
        return redirect(url_for('list_chws'))
    
    if request.method == 'POST':
        chw.name = request.form['name']
        chw.village = request.form['village']
        chw.district = request.form['district']
        chw.phone = request.form['phone']
        chw.is_active = 'is_active' in request.form
        flash(f'CHW {chw.name} updated successfully!', 'success')
        return redirect(url_for('list_chws'))
    
    districts = ["Turkana", "Elgeyo-Marakwet", "Kajiado", "Nairobi", "Marsabit", "Garissa"]
    return render_template('chw_form.html', chw=chw, districts=districts)

@app.route('/chws/<chw_id>/delete', methods=['POST'])
def delete_chw(chw_id):
    """Delete CHW"""
    global chws
    chw = next((c for c in chws if c.id == chw_id), None)
    if chw:
        chws = [c for c in chws if c.id != chw_id]
        flash(f'CHW {chw.name} deleted successfully!', 'success')
    return redirect(url_for('list_chws'))

@app.route('/chws/<chw_id>')
def view_chw(chw_id):
    """View CHW details with their patients and visits"""
    print(f"Looking for CHW with ID: {chw_id}")  # Debug print
    print(f"Available CHW IDs: {[c.id for c in chws]}")  # Debug print
    
    chw = next((c for c in chws if c.id == chw_id), None)
    if not chw:
        print(f"CHW {chw_id} not found!")  # Debug print
        flash(f'CHW with ID {chw_id} not found!', 'error')
        return redirect(url_for('list_chws'))
    
    chw_patients = [p for p in patients if p.chw_id == chw_id]
    chw_visits = [v for v in visits if v.chw_id == chw_id]
    
    # Statistics
    total_patients = len(chw_patients)
    total_visits = len(chw_visits)
    visits_this_month = len([v for v in chw_visits 
                            if v.visit_date > datetime.now() - timedelta(days=30)])
    patients_needing_visits = len([p for p in chw_patients if p.needs_visit()])
    
    return render_template('chw_view.html',
                         chw=chw,
                         patients=chw_patients,
                         visits=sorted(chw_visits, key=lambda x: x.visit_date, reverse=True)[:20],
                         total_patients=total_patients,
                         total_visits=total_visits,
                         visits_this_month=visits_this_month,
                         patients_needing_visits=patients_needing_visits)

# ============== PATIENT CRUD ROUTES ==============

@app.route('/patients')
def list_patients():
    """List all patients"""
    chw_id = request.args.get('chw_id')
    needs_visit = request.args.get('needs_visit')
    
    filtered_patients = patients
    if chw_id:
        filtered_patients = [p for p in filtered_patients if p.chw_id == chw_id]
    if needs_visit:
        filtered_patients = [p for p in filtered_patients if p.needs_visit()]
    
    return render_template('patient_list.html', 
                         patients=filtered_patients,
                         chws=chws,
                         selected_chw=chw_id)

@app.route('/patients/new', methods=['GET', 'POST'])
def create_patient():
    """Create new patient"""
    if request.method == 'POST':
        new_id = f"PAT{len(patients)+1:04d}"
        patient = Patient(
            id=new_id,
            name=request.form['name'],
            age=int(request.form['age']),
            village=request.form['village'],
            chw_id=request.form['chw_id'],
            is_pregnant='is_pregnant' in request.form,
            has_chronic_condition='has_chronic_condition' in request.form
        )
        patients.append(patient)
        
        # Add to CHW's patient list
        chw = next((c for c in chws if c.id == patient.chw_id), None)
        if chw:
            chw.patients_assigned.append(patient.id)
        
        flash(f'Patient {patient.name} registered successfully!', 'success')
        return redirect(url_for('list_patients'))
    
    return render_template('patient_form.html', patient=None, chws=chws)

@app.route('/patients/<patient_id>/edit', methods=['GET', 'POST'])
def edit_patient(patient_id):
    """Edit patient"""
    patient = next((p for p in patients if p.id == patient_id), None)
    if not patient:
        flash('Patient not found!', 'error')
        return redirect(url_for('list_patients'))
    
    if request.method == 'POST':
        patient.name = request.form['name']
        patient.age = int(request.form['age'])
        patient.village = request.form['village']
        
        # Handle CHW reassignment
        new_chw_id = request.form['chw_id']
        if new_chw_id != patient.chw_id:
            # Remove from old CHW
            old_chw = next((c for c in chws if c.id == patient.chw_id), None)
            if old_chw and patient.id in old_chw.patients_assigned:
                old_chw.patients_assigned.remove(patient.id)
            
            # Add to new CHW
            patient.chw_id = new_chw_id
            new_chw = next((c for c in chws if c.id == new_chw_id), None)
            if new_chw:
                new_chw.patients_assigned.append(patient.id)
        
        patient.is_pregnant = 'is_pregnant' in request.form
        patient.has_chronic_condition = 'has_chronic_condition' in request.form
        
        flash(f'Patient {patient.name} updated successfully!', 'success')
        return redirect(url_for('view_patient', patient_id=patient.id))
    
    return render_template('patient_form.html', patient=patient, chws=chws)

@app.route('/patients/<patient_id>')
def view_patient(patient_id):
    """View patient details"""
    patient = next((p for p in patients if p.id == patient_id), None)
    if not patient:
        flash('Patient not found!', 'error')
        return redirect(url_for('list_patients'))
    
    chw = next((c for c in chws if c.id == patient.chw_id), None)
    patient_visits = [v for v in visits if v.patient_id == patient_id]
    
    return render_template('patient_view.html',
                         patient=patient,
                         chw=chw,
                         visits=sorted(patient_visits, key=lambda x: x.visit_date, reverse=True))

# ============== VISIT CRUD ROUTES ==============

@app.route('/visits/new', methods=['GET', 'POST'])
def create_visit():
    """Record a new health visit"""
    if request.method == 'POST':
        new_id = f"VIS{len(visits)+1:05d}"
        visit = HealthVisit(
            id=new_id,
            patient_id=request.form['patient_id'],
            chw_id=request.form['chw_id'],
            visit_date=datetime.strptime(request.form['visit_date'], '%Y-%m-%d'),
            visit_type=request.form['visit_type'],
            notes=request.form['notes'],
            is_offline_sync='is_offline_sync' in request.form
        )
        visits.append(visit)
        
        # Update patient's last visit
        patient = next((p for p in patients if p.id == visit.patient_id), None)
        if patient:
            patient.last_visit_date = visit.visit_date
        
        flash('Visit recorded successfully!', 'success')
        return redirect(url_for('index'))
    
    # Pre-select patient if specified
    patient_id = request.args.get('patient_id')
    chw_id = request.args.get('chw_id')
    
    return render_template('visit_form.html', 
                         patients=patients, 
                         chws=chws,
                         selected_patient=patient_id,
                         selected_chw=chw_id,
                         today=datetime.now().strftime('%Y-%m-%d'))

# ============== API ROUTES FOR DASHBOARD ==============

@app.route('/api/stats')
@jwt_required(optional=True)
def api_stats():
    """JSON API for dashboard updates"""
    return jsonify({
        'total_chws': len(chws),
        'total_patients': len(patients),
        'total_visits': len(visits),
        'active_chws': len([c for c in chws if c.is_active]),
        'visits_this_week': len([v for v in visits 
                                if v.visit_date > datetime.now() - timedelta(days=7)]),
        'patients_needing_visits': len([p for p in patients if p.needs_visit()])
    })

@app.route('/api/district_stats')
def api_district_stats():
    """District-level statistics for charts"""
    stats = {}
    for chw in chws:
        if chw.district not in stats:
            stats[chw.district] = {
                'chws': 0,
                'patients': 0,
                'visits': 0
            }
        stats[chw.district]['chws'] += 1
    
    for patient in patients:
        chw = next((c for c in chws if c.id == patient.chw_id), None)
        if chw and chw.district in stats:
            stats[chw.district]['patients'] += 1
    
    for visit in visits:
        chw = next((c for c in chws if c.id == visit.chw_id), None)
        if chw and chw.district in stats:
            stats[chw.district]['visits'] += 1
    
    return jsonify(stats)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏥 ICT4D Health Worker CRUD App with Dashboard")
    print("="*60)
    print("\n📍 Access the application:")
    print("   - Main Dashboard: http://localhost:5000")
    print("   - GraphQL API: http://localhost:5000/graphql")
    print("   - REST API: http://localhost:5000/api/stats")
    print("\n📋 Features:")
    print("   ✓ Complete CRUD for CHWs, Patients, Visits")
    print("   ✓ Interactive Dashboard with key metrics")
    print("   ✓ District-level analytics")
    print("   ✓ Mobile-friendly interface")
    print("   ✓ Offline-ready data collection")
    print("\n" + "="*60)
    
    app.run(debug=True, port=5000)