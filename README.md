# EventPlanner Backup API - Documentation

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

A RESTful API for backing up and recovering event planning data, built with FastAPI and SQLite.

## Table of Contents
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Data Models](#data-models)
- [Setup & Installation](#setup--installation)
- [Usage Examples](#usage-examples)
- [Database Schema](#database-schema)
- [License](#license)

## Features
- Secure backup of complete user event data
- Recovery of all event-related information
- SQLite database storage
- Data validation with Pydantic models
- RESTful endpoints with proper HTTP status codes

## API Endpoints

### 1. Backup Data
- **POST** `/backup`
  - Stores complete user data including:
    - User profile
    - Active events
    - Archived events
    - Tasks
    - Guest lists
  - Request body: `BackupRequest` model
  - Returns: `BackupResponse` with status and timestamp

### 2. Recover Data
- **GET** `/recover/{user_id}`
  - Retrieves all backup data for a specific user
  - Returns: Complete user data structure

## Data Models

### Core Models:
- **User**: `id, username, password_hash, email`
- **Event**: `id, user_id, name, date, time, venue, description, is_archived`
- **ArchivedEvent**: Extends Event with `archived_date`
- **Task**: `id, event_id, description, is_completed`
- **Guest**: `id, event_id, name, email`

### Request/Response:
- **BackupRequest**: Contains all data to be backed up + timestamp
- **BackupResponse**: Confirmation message + timestamp

## Setup & Installation

1. **Prerequisites**:
   - Python 3.7+
   - pip package manager

2. **Install dependencies**:
   ```bash
   pip install fastapi uvicorn pydantic sqlite3
   ```

3. **Run the API**:
   ```bash
   uvicorn eventon:app --reload
   ```

4. **Access docs**:
   - Interactive docs: http://127.0.0.1:8000/docs
   - OpenAPI schema: http://127.0.0.1:8000/redoc

## Usage Examples

### Backup Data (POST /backup)
```python
import requests
import datetime

url = "http://localhost:8000/backup"
data = {
    "user_id": 1,
    "timestamp": datetime.datetime.now().isoformat(),
    "user": {
        "id": 1,
        "username": "event_planner",
        "password_hash": "hashed_password_123",
        "email": "user@example.com"
    },
    "events": [...],
    "archived_events": [...],
    "tasks": [...],
    "guests": [...]
}

response = requests.post(url, json=data)
print(response.json())
```

### Recover Data (GET /recover/{user_id})
```python
import requests

user_id = 1
response = requests.get(f"http://localhost:8000/recover/{user_id}")
print(response.json())
```

## Database Schema
The SQLite database (`backup.db`) contains these tables:
1. **users**: User account information
2. **events**: Active events
3. **archived_events**: Historical events
4. **tasks**: Event tasks
5. **guests**: Event guest lists

All tables include a `backup_timestamp` field tracking when the data was stored.

## License
MIT License - Free for personal and commercial use.
