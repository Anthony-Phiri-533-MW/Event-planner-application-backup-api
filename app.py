from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List, Optional

app = FastAPI(title="EventPlanner Backup API")

# Pydantic models for request/response validation
class User(BaseModel):
    id: int
    username: str
    password_hash: str
    email: Optional[str]

class Event(BaseModel):
    id: int
    user_id: int
    name: str
    date: str
    time: Optional[str]
    venue: Optional[str]
    description: Optional[str]
    is_archived: bool

class ArchivedEvent(BaseModel):
    id: int
    user_id: int
    name: str
    date: str
    time: Optional[str]
    venue: Optional[str]
    description: Optional[str]
    archived_date: str

class Task(BaseModel):
    id: int
    event_id: int
    description: str
    is_completed: bool

class Guest(BaseModel):
    id: int
    event_id: int
    name: str
    email: Optional[str]

class BackupRequest(BaseModel):
    user_id: int
    user: User
    events: List[Event]
    archived_events: List[ArchivedEvent]
    tasks: List[Task]
    guests: List[Guest]
    timestamp: str

class BackupResponse(BaseModel):
    message: str
    timestamp: str

# SQLite database helper
class BackupDatabase:
    def __init__(self, db_name="backup.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    backup_timestamp TEXT
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT,
                    venue TEXT,
                    description TEXT,
                    is_archived INTEGER DEFAULT 0,
                    backup_timestamp TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS archived_events (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT,
                    venue TEXT,
                    description TEXT,
                    archived_date TEXT,
                    backup_timestamp TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    is_completed INTEGER DEFAULT 0,
                    backup_timestamp TEXT,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS guests (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT,
                    backup_timestamp TEXT,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            ''')

    def backup_user(self, user: User, timestamp: str):
        with self.conn:
            try:
                self.conn.execute('''
                    INSERT OR REPLACE INTO users (id, username, password_hash, email, backup_timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user.id, user.username, user.password_hash, user.email, timestamp))
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail="User backup failed due to database constraints")

    def backup_events(self, events: List[Event], timestamp: str):
        with self.conn:
            for event in events:
                self.conn.execute('''
                    INSERT OR REPLACE INTO events (id, user_id, name, date, time, venue, description, is_archived, backup_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.id, event.user_id, event.name, event.date, event.time,
                    event.venue, event.description, 1 if event.is_archived else 0, timestamp
                ))

    def backup_archived_events(self, archived_events: List[ArchivedEvent], timestamp: str):
        with self.conn:
            for archived_event in archived_events:
                self.conn.execute('''
                    INSERT OR REPLACE INTO archived_events (id, user_id, name, date, time, venue, description, archived_date, backup_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    archived_event.id, archived_event.user_id, archived_event.name, archived_event.date,
                    archived_event.time, archived_event.venue, archived_event.description,
                    archived_event.archived_date, timestamp
                ))

    def backup_tasks(self, tasks: List[Task], timestamp: str):
        with self.conn:
            for task in tasks:
                self.conn.execute('''
                    INSERT OR REPLACE INTO tasks (id, event_id, description, is_completed, backup_timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    task.id, task.event_id, task.description, 1 if task.is_completed else 0, timestamp
                ))

    def backup_guests(self, guests: List[Guest], timestamp: str):
        with self.conn:
            for guest in guests:
                self.conn.execute('''
                    INSERT OR REPLACE INTO guests (id, event_id, name, email, backup_timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (guest.id, guest.event_id, guest.name, guest.email, timestamp))

    def get_backup(self, user_id: int):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, username, password_hash, email, backup_timestamp FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            cursor.execute('SELECT id, user_id, name, date, time, venue, description, is_archived, backup_timestamp FROM events WHERE user_id = ?', (user_id,))
            events = cursor.fetchall()
            cursor.execute('SELECT id, user_id, name, date, time, venue, description, archived_date, backup_timestamp FROM archived_events WHERE user_id = ?', (user_id,))
            archived_events = cursor.fetchall()
            cursor.execute('SELECT id, event_id, description, is_completed, backup_timestamp FROM tasks WHERE event_id IN (SELECT id FROM events WHERE user_id = ?)', (user_id,))
            tasks = cursor.fetchall()
            cursor.execute('SELECT id, event_id, name, email, backup_timestamp FROM guests WHERE event_id IN (SELECT id FROM events WHERE user_id = ?)', (user_id,))
            guests = cursor.fetchall()
            return {
                'user_id': user_id,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'password_hash': user[2],
                    'email': user[3]
                },
                'events': [
                    {
                        'id': row[0], 'user_id': row[1], 'name': row[2], 'date': row[3],
                        'time': row[4], 'venue': row[5], 'description': row[6],
                        'is_archived': bool(row[7]), 'backup_timestamp': row[8]
                    } for row in events
                ],
                'archived_events': [
                    {
                        'id': row[0], 'user_id': row[1], 'name': row[2], 'date': row[3],
                        'time': row[4], 'venue': row[5], 'description': row[6],
                        'archived_date': row[7], 'backup_timestamp': row[8]
                    } for row in archived_events
                ],
                'tasks': [
                    {
                        'id': row[0], 'event_id': row[1], 'description': row[2],
                        'is_completed': bool(row[3]), 'backup_timestamp': row[4]
                    } for row in tasks
                ],
                'guests': [
                    {
                        'id': row[0], 'event_id': row[1], 'name': row[2], 'email': row[3],
                        'backup_timestamp': row[4]
                    } for row in guests
                ],
                'timestamp': user[4]  # Latest backup timestamp
            }

# Initialize database
db = BackupDatabase()

@app.post("/backup", response_model=BackupResponse)
async def backup_data(data: BackupRequest):
    try:
        # Store backup data with timestamp
        db.backup_user(data.user, data.timestamp)
        db.backup_events(data.events, data.timestamp)
        db.backup_archived_events(data.archived_events, data.timestamp)
        db.backup_tasks(data.tasks, data.timestamp)
        db.backup_guests(data.guests, data.timestamp)
        return {"message": "Backup completed successfully", "timestamp": data.timestamp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@app.get("/recover/{user_id}")
async def recover_data(user_id: int):
    try:
        return db.get_backup(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recovery failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
