from flask import Flask, jsonify
from strawberry.flask.views import GraphQLView
from schemas.health_schema import schema
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Add GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enables the GraphiQL interface
    )
)

@app.route('/')
def index():
    """Welcome page with ICT4D context"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ICT4D Health Monitor</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #2c3e50; }
            .card { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
            code { background: #e9ecef; padding: 2px 5px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🏥 ICT4D Community Health Worker Monitoring System</h1>
        <div class="card">
            <h2>Demonstrating Key ICT4D Competencies:</h2>
            <ul>
                <li><strong>Low-bandwidth optimized</strong> - GraphQL reduces data transfer</li>
                <li><strong>Offline-first design</strong> - Supports remote areas [citation:7]</li>
                <li><strong>MEAL dashboards</strong> - Built-in analytics for reporting [citation:1]</li>
                <li><strong>Mobile-friendly</strong> - Works with React Native/Flutter apps</li>
                <li><strong>Government reporting</strong> - District-level summaries [citation:2]</li>
            </ul>
        </div>
        
        <h3>🚀 Try these queries in <a href="/graphql">GraphiQL Interface</a>:</h3>
        
        <h4>1. District Overview (for government stakeholders):</h4>
        <code>
        {
          districtSummary(district: "Turkana") {
            district
            totalChws
            totalPatients
            totalVisits
            activeChws
            patientToChwRatio
          }
        }
        </code>
        
        <h4>2. Patients needing follow-up (proactive care):</h4>
        <code>
        {
          patientsNeedingVisits(daysThreshold: 30) {
            name
            village
            assignedChw {
              name
              phone
            }
          }
        }
        </code>
        
        <h4>3. Offline sync report (technology adoption):</h4>
        <code>
        {
          offlineSyncStatus {
            totalOfflineVisits
            uniqueChwsOffline
            lastWeekOffline
            offlineAdoptionRate
          }
        }
        </code>
        
        <h4>4. CHW performance dashboard:</h4>
        <code>
        {
          healthWorkers(district: "Kajiado") {
            name
            yearsActive
            visitStats {
              totalVisits
              emergencyVisits
              completionRate
            }
            recentVisits(days: 7) {
              visitType
              patient {
                name
              }
            }
          }
        }
        </code>
        
        <div class="card">
            <h3>📊 MEAL Dashboard Features:</h3>
            <ul>
                <li>Track patient-CHW ratios for workload balancing</li>
                <li>Monitor emergency vs routine visit patterns</li>
                <li>Offline adoption rates for technology assessment</li>
                <li>District-level aggregation for reporting to Ministry of Health</li>
            </ul>
        </div>
        
        <p><small>Built with Strawberry GraphQL - Demonstrating Python/Django/Flask proficiency [citation:2]</small></p>
    </body>
    </html>
    """

@app.route('/api/dashboard/<district>')
def dashboard_api(district):
    """REST endpoint for dashboard - shows hybrid API skills"""
    from schemas.health_schema import Query
    from data.sample_data import generate_sample_data
    
    chws, patients, visits = generate_sample_data()
    district_chws = [c for c in chws if c.district == district]
    
    return jsonify({
        "district": district,
        "stats": {
            "chws": len(district_chws),
            "active_chws": len([c for c in district_chws if c.is_active]),
            "patients": len([p for p in patients if p.village in [c.village for c in district_chws]]),
            "visits_last_month": len([v for v in visits if v.visit_date > datetime.now() - timedelta(days=30)])
        }
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 ICT4D Health Monitor Server Starting...")
    print("="*50)
    print("\n📍 Access the application:")
    print("   - Main interface: http://localhost:5000")
    print("   - GraphQL playground: http://localhost:5000/graphql")
    print("\n📋 This project demonstrates:")
    print("   ✓ Python/Flask/GraphQL (from job requirements [citation:2])")
    print("   ✓ Data modeling for development programs")
    print("   ✓ MEAL-ready dashboards")
    print("   ✓ Offline-first architecture patterns")
    print("   ✓ Stakeholder-friendly reporting")
    print("\n" + "="*50)
    
    app.run(debug=True, port=5000)