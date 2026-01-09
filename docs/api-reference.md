# API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication

Currently uses API keys (to be implemented). For development, all endpoints are accessible.

## Flights

### List Flights
```http
GET /flights/
```

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100)
- `status` (string): Filter by status
- `airline` (string): Filter by airline code
- `date` (string): Filter by date (YYYY-MM-DD)

**Response:**
```json
[
  {
    "id": 1,
    "flight_number": "TK001",
    "airline_code": "TK",
    "airline_name": "Turkish Airlines",
    "aircraft_type": "A321",
    "status": "scheduled",
    "gate": "A12",
    "scheduled_time": "2024-01-09T10:30:00Z",
    "predicted_delay": 15
  }
]
```

### Get Flight
```http
GET /flights/{flight_id}
```

### Create Flight
```http
POST /flights/
```

**Request Body:**
```json
{
  "flight_number": "TK001",
  "airline_code": "TK",
  "airline_name": "Turkish Airlines",
  "flight_type": "departure",
  "aircraft_type": "A321",
  "origin_airport": "IST",
  "destination_airport": "LHR",
  "scheduled_time": "2024-01-09T10:30:00Z"
}
```

### Update Flight
```http
PATCH /flights/{flight_id}
```

## Turnarounds

### List Turnarounds
```http
GET /turnarounds/
```

**Query Parameters:**
- `skip`, `limit`: Pagination
- `status`: Filter by status
- `gate`: Filter by gate

### Get Turnaround
```http
GET /turnarounds/{turnaround_id}
```

**Response:**
```json
{
  "id": 1,
  "turnaround_id": "TRN-001",
  "status": "in_progress",
  "flight_id": 1,
  "gate": "A12",
  "scheduled_start": "2024-01-09T10:00:00Z",
  "scheduled_end": "2024-01-09T11:00:00Z",
  "risk_score": 0.35,
  "completion_percentage": 45.0,
  "activities": [...]
}
```

### Get At-Risk Turnarounds
```http
GET /turnarounds/at-risk/list?risk_threshold=0.5
```

### Get Active Turnarounds (Dashboard)
```http
GET /turnarounds/active/dashboard
```

## Alerts

### List Alerts
```http
GET /alerts/
```

### Get Alert
```http
GET /alerts/{alert_id}
```

### Create Alert
```http
POST /alerts/
```

**Request Body:**
```json
{
  "alert_type": "delay_prediction",
  "severity": "warning",
  "title": "Delay Predicted",
  "message": "Flight TK001 predicted to experience 15-minute delay",
  "flight_id": 1,
  "predicted_delay_minutes": 15
}
```

### Acknowledge Alert
```http
POST /alerts/{alert_id}/acknowledge?acknowledged_by=user@example.com
```

### Resolve Alert
```http
POST /alerts/{alert_id}/resolve?resolved_by=user@example.com&resolution_notes=Fixed
```

### Get Active Alerts
```http
GET /alerts/active/list?severity=critical
```

## Analytics

### Delay Statistics
```http
GET /analytics/delays?hours=24&airline=TK
```

**Response:**
```json
{
  "total_flights": 150,
  "delayed_flights": 23,
  "average_delay_minutes": 12.5,
  "on_time_percentage": 84.7,
  "most_delayed_airline": "TK"
}
```

### Turnaround Statistics
```http
GET /analytics/turnarounds?hours=24
```

**Response:**
```json
{
  "total_turnarounds": 145,
  "completed_on_time": 120,
  "at_risk": 15,
  "delayed": 10,
  "average_duration_minutes": 52.3
}
```

### Dashboard Summary
```http
GET /analytics/dashboard/summary
```

### Hourly Performance
```http
GET /analytics/performance/hourly?hours=24
```

## WebSocket

### Real-Time Updates
```
ws://localhost:8000/ws
```

**Message Format:**
```json
{
  "type": "turnaround_update",
  "data": {
    "turnaround_id": "TRN-001",
    "status": "at_risk",
    "risk_score": 0.75
  },
  "timestamp": "2024-01-09T10:30:00Z"
}
```

## Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

- Development: No limits
- Production: 1000 requests/hour per API key

## Error Response Format

```json
{
  "detail": "Error message",
  "field": "field_name"
}
```
