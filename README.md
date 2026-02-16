# ICT4D Community Health Worker Monitoring System

## 🎯 Project Overview
A GraphQL-based monitoring system for Community Health Worker programs in low-resource settings. Built to demonstrate competencies required for ICT4D Officer roles in international development organizations.

## 🛠️ Technical Stack
- **Backend**: Python 3.11 + Flask + Strawberry GraphQL
- **Data Modeling**: Dataclasses with offline-first considerations
- **API Design**: GraphQL with field-level documentation
- **Deployment Ready**: Includes MEAL dashboards and government reporting features

## 🏗️ Architecture Highlights

### 1. Offline-First Design [citation:7]
```python
# Models include offline sync flags
is_offline_sync: bool = False  # Tracks data collected without internet

# Queries monitor adoption
offlineSyncStatus {
  offlineAdoptionRate  # Measures technology uptake
}