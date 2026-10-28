import sqlite3
import hashlib
import json
import os
from datetime import datetime

class UserDatabase:
    def __init__(self, db_path="data/users/users.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.create_tables()
        self.seed_default_data()

    def _get_connection(self):
        """Helper method to get a database connection with row access by name."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        """Creates all necessary tables for Titans Fitness Studio."""
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            full_name TEXT NOT NULL,
            avatar TEXT DEFAULT 'TT',
            is_locked BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS member_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            member_code TEXT UNIQUE NOT NULL,
            membership_plan TEXT NOT NULL,
            monthly_fee INTEGER DEFAULT 4499,
            status TEXT DEFAULT 'Active',
            streak_days INTEGER DEFAULT 12,
            workouts_done INTEGER DEFAULT 4,
            workouts_target INTEGER DEFAULT 5,
            calories_burned INTEGER DEFAULT 2840,
            water_ml INTEGER DEFAULT 2250,
            water_target_ml INTEGER DEFAULT 3500,
            protein_g INTEGER DEFAULT 142,
            protein_target_g INTEGER DEFAULT 180,
            assigned_coach TEXT DEFAULT 'Coach Ananya Verma',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );

        CREATE TABLE IF NOT EXISTS member_workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            sets_reps TEXT NOT NULL,
            target_tag TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );

        CREATE TABLE IF NOT EXISTS studio_classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            coach TEXT NOT NULL,
            time_str TEXT NOT NULL,
            ampm_str TEXT NOT NULL,
            studio_room TEXT NOT NULL,
            duration_mins INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trainer_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            client_code TEXT NOT NULL,
            avatar TEXT NOT NULL,
            goal TEXT NOT NULL,
            session_time TEXT NOT NULL,
            status TEXT NOT NULL,
            badge_class TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trainer_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER NOT NULL,
            time_str TEXT NOT NULL,
            title TEXT NOT NULL,
            subtitle TEXT NOT NULL,
            status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS maintenance_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_name TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            status_pill TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS assigned_routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER,
            client_name TEXT NOT NULL,
            template_name TEXT NOT NULL,
            notes TEXT,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self._get_connection() as conn:
            conn.executescript(schema)
            conn.commit()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def seed_default_data(self):
        """Seeds initial demo accounts and studio metrics if database is fresh."""
        with self._get_connection() as conn:
            user_count = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
            if user_count > 0:
                return

            # Default Users: Admin/Owner, Member, Trainer
            default_users = [
                ("admin", "admin@123", "gym123", "admin", "Rajesh Singhania", "RS"),
                ("owner", "admin@titans.com", "gym123", "admin", "Rajesh Singhania", "RS"),
                ("rohan", "rohan.sharma@gmail.com", "gym123", "member", "Rohan Sharma", "RS"),
                ("member", "member@titans.com", "gym123", "member", "Rohan Sharma", "RS"),
                ("ananya", "ananya.verma@titans.com", "gym123", "trainer", "Coach Ananya Verma", "AV"),
                ("trainer", "trainer@titans.com", "gym123", "trainer", "Coach Ananya Verma", "AV")
            ]

            for username, email, pwd, role, full_name, avatar in default_users:
                conn.execute(
                    """INSERT OR IGNORE INTO users (username, email, password, role, full_name, avatar)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (username, email, self._hash_password(pwd), role, full_name, avatar)
                )

            # Get user IDs
            rohan = conn.execute("SELECT user_id FROM users WHERE username = 'rohan'").fetchone()
            ananya = conn.execute("SELECT user_id FROM users WHERE username = 'ananya'").fetchone()

            if rohan:
                rohan_id = rohan["user_id"]
                conn.execute(
                    """INSERT OR IGNORE INTO member_profiles (
                        user_id, member_code, membership_plan, monthly_fee, status, streak_days,
                        workouts_done, workouts_target, calories_burned, water_ml, water_target_ml,
                        protein_g, protein_target_g, assigned_coach
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (rohan_id, "#TITAN-9204", "Titan Elite", 4499, "Active", 12, 4, 5, 2840, 2250, 3500, 142, 180, "Coach Ananya Verma")
                )

                workouts = [
                    (rohan_id, "Barbell Bench Press", "4 Sets • 8-10 Reps • 85 kg target", "Chest", 1),
                    (rohan_id, "Incline Dumbbell Press", "3 Sets • 10-12 Reps • 26 kg", "Upper Chest", 0),
                    (rohan_id, "Cable Chest Flyes", "3 Sets • 15 Reps • High to Low", "Isolation", 0),
                    (rohan_id, "Tricep Rope Pushdowns", "4 Sets • 12 Reps • Superset with Dips", "Triceps", 0)
                ]
                for w in workouts:
                    conn.execute(
                        "INSERT INTO member_workouts (user_id, exercise_name, sets_reps, target_tag, is_completed) VALUES (?, ?, ?, ?, ?)",
                        w
                    )

            # Classes
            classes = [
                ("HIIT Desi Power Shred", "Coach Kabir Malhotra", "06:00", "PM TODAY", "Studio A", 45),
                ("Power Vinyasa & Core Mobility", "Coach Ananya Verma", "08:30", "AM TOMORROW", "Zen Studio", 60)
            ]
            for c in classes:
                conn.execute(
                    "INSERT INTO studio_classes (title, coach, time_str, ampm_str, studio_room, duration_mins) VALUES (?, ?, ?, ?, ?, ?)",
                    c
                )

            # Trainer Clients
            trainer_id = ananya["user_id"] if ananya else 1
            clients = [
                (trainer_id, "Rohan Sharma", "#TITAN-9204", "RS", "Goal: Hypertrophy & Strength • Today: Push Day", "Session @ 11:30 AM", "Active", "badge-active"),
                (trainer_id, "Devansh Patel", "#TITAN-8812", "DP", "Goal: Fat Loss & Conditioning • 8 Weeks In", "Session @ 02:00 PM", "Active", "badge-active"),
                (trainer_id, "Priya Nair", "#TITAN-7319", "PN", "Goal: Mobility & Deadlift Form Correction", "Needs New Program", "Pending", "badge-pending"),
                (trainer_id, "Siddharth Rao", "#TITAN-5541", "SR", "Goal: Powerlifting Peaking • Squat 180kg", "Session @ 04:30 PM", "Active", "badge-active")
            ]
            for cl in clients:
                conn.execute(
                    """INSERT INTO trainer_clients (trainer_id, client_name, client_code, avatar, goal, session_time, status, badge_class)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    cl
                )

            # Trainer Schedule
            sessions = [
                (trainer_id, "09:00 AM", "Session: Kavya Iyer", "Full Body Mobility & Core Stabilization • Completed ✓", "Finished"),
                (trainer_id, "11:30 AM", "1-on-1: Rohan Sharma", "Upper Body Push & Rotator Cuff Health • Free Weights Area", "Upcoming"),
                (trainer_id, "05:30 PM", "Group Studio Batch: Titan Shakti Strength", "Main Floor • 16 Registered Athletes", "Scheduled")
            ]
            for s in sessions:
                conn.execute(
                    "INSERT INTO trainer_sessions (trainer_id, time_str, title, subtitle, status) VALUES (?, ?, ?, ?, ?)",
                    s
                )

            # Maintenance Tickets
            tickets = [
                ("Jerai Fitness Commercial Treadmill #4", "Scheduled motor & belt servicing • Engineer arriving 4 PM", "Service Due", "pill-expiring"),
                ("Being Strong Dual Cable Cross", "Inspected & lubricated Oct 20", "100% Operational", "pill-paid"),
                ("Studio HVAC & Daikin Air Purifiers", "Optimal airflow • PM2.5: 8 µg/m³ (HEPA filter clean)", "Normal", "pill-paid")
            ]
            for t in tickets:
                conn.execute(
                    "INSERT INTO maintenance_tickets (equipment_name, description, status, status_pill) VALUES (?, ?, ?, ?)",
                    t
                )

            conn.commit()

    def add_user(self, username: str, email: str, password: str, role: str = "member", full_name: str = ""):
        """Adds a new user to the database."""
        username = username.strip().lower()
        email = email.strip().lower()
        hashed_password = self._hash_password(password)
        if not full_name:
            full_name = username.capitalize()
        avatar = "".join([part[0].upper() for part in full_name.split()][:2]) or "TT"

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO users (username, email, password, role, full_name, avatar)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (username, email, hashed_password, role, full_name, avatar)
                )
                user_id = cursor.lastrowid
                if role == "member":
                    conn.execute(
                        """INSERT INTO member_profiles (user_id, member_code, membership_plan, monthly_fee, status)
                           VALUES (?, ?, ?, ?, ?)""",
                        (user_id, f"#TITAN-{1000 + user_id}", "Titan Pro", 2999, "Active")
                    )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_login(self, identifier: str, password: str):
        """Verifies login by username or email. Accepts both hashed and plain (for legacy/admin)."""
        identifier = identifier.strip().lower()
        hashed_attempt = self._hash_password(password)

        with self._get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?",
                (identifier, identifier)
            ).fetchone()

        if not user:
            return None

        # Check hash match or plain password fallback
        if user["password"] == hashed_attempt or user["password"] == password:
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "full_name": user["full_name"],
                "avatar": user["avatar"]
            }
        return None

    def get_member_data(self, user_id: int = None):
        """Fetches all member dashboard metrics and workouts."""
        with self._get_connection() as conn:
            if user_id:
                profile = conn.execute("SELECT * FROM member_profiles WHERE user_id = ?", (user_id,)).fetchone()
            else:
                profile = conn.execute("SELECT * FROM member_profiles LIMIT 1").fetchone()

            if not profile:
                profile = {
                    "member_code": "#TITAN-9204", "membership_plan": "Titan Elite", "monthly_fee": 4499,
                    "status": "Active", "streak_days": 12, "workouts_done": 4, "workouts_target": 5,
                    "calories_burned": 2840, "water_ml": 2250, "water_target_ml": 3500,
                    "protein_g": 142, "protein_target_g": 180, "assigned_coach": "Coach Ananya Verma"
                }
            else:
                profile = dict(profile)

            uid = profile.get("user_id", user_id or 1)
            workouts = conn.execute("SELECT * FROM member_workouts WHERE user_id = ?", (uid,)).fetchall()
            classes = conn.execute("SELECT * FROM studio_classes").fetchall()

            return {
                "profile": profile,
                "workouts": [dict(w) for w in workouts],
                "classes": [dict(c) for c in classes]
            }

    def update_water(self, amount: int = None, reset: bool = False, user_id: int = None):
        """Updates water intake."""
        with self._get_connection() as conn:
            if user_id:
                row = conn.execute("SELECT water_ml, water_target_ml FROM member_profiles WHERE user_id = ?", (user_id,)).fetchone()
            else:
                row = conn.execute("SELECT water_ml, water_target_ml FROM member_profiles LIMIT 1").fetchone()

            current = row["water_ml"] if row else 2250
            target = row["water_target_ml"] if row else 3500

            new_val = 0 if reset else max(0, current + (amount or 0))

            if user_id:
                conn.execute("UPDATE member_profiles SET water_ml = ? WHERE user_id = ?", (new_val, user_id))
            else:
                conn.execute("UPDATE member_profiles SET water_ml = ?", (new_val,))
            conn.commit()

            pct = min(100, int((new_val / target) * 100)) if target > 0 else 0
            return {"water_ml": new_val, "water_target_ml": target, "pct": pct}

    def toggle_workout(self, workout_id: int):
        """Toggles workout completion state."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT is_completed FROM member_workouts WHERE id = ?", (workout_id,)).fetchone()
            if not row:
                return None
            new_state = 0 if row["is_completed"] else 1
            conn.execute("UPDATE member_workouts SET is_completed = ? WHERE id = ?", (new_state, workout_id))
            conn.commit()
            return {"id": workout_id, "is_completed": bool(new_state)}

    def get_trainer_data(self, trainer_id: int = None):
        """Fetches trainer roster, sessions, and statistics."""
        with self._get_connection() as conn:
            clients = conn.execute("SELECT * FROM trainer_clients").fetchall()
            sessions = conn.execute("SELECT * FROM trainer_sessions").fetchall()
            return {
                "stats": {
                    "active_athletes": 28,
                    "today_sessions": 6,
                    "client_adherence": "94.2%",
                    "monthly_payout": "₹72,500"
                },
                "clients": [dict(c) for c in clients],
                "sessions": [dict(s) for s in sessions]
            }

    def assign_routine(self, trainer_id: int, client_name: str, template_name: str, notes: str):
        """Stores a routine assigned to an athlete."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO assigned_routines (trainer_id, client_name, template_name, notes) VALUES (?, ?, ?, ?)",
                (trainer_id, client_name, template_name, notes)
            )
            conn.commit()
        return {"status": "success", "message": f"Routine '{template_name}' successfully pushed to {client_name}!"}

    def get_admin_data(self):
        """Fetches admin overview metrics, recent members, and maintenance."""
        with self._get_connection() as conn:
            tickets = conn.execute("SELECT * FROM maintenance_tickets").fetchall()
            return {
                "stats": {
                    "monthly_revenue": "₹42.85 L",
                    "mrr_growth": "+11.4%",
                    "active_members": 1420,
                    "new_enrollments": 64,
                    "floor_occupancy": 74,
                    "floor_capacity": 120,
                    "occupancy_pct": 62,
                    "equipment_health": "97.5%"
                },
                "tickets": [dict(t) for t in tickets]
            }

    def add_maintenance_ticket(self, equipment_name: str, description: str, status: str = "Service Due", status_pill: str = "pill-expiring"):
        """Logs a new maintenance ticket."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO maintenance_tickets (equipment_name, description, status, status_pill) VALUES (?, ?, ?, ?)",
                (equipment_name, description, status, status_pill)
            )
            conn.commit()
            return {"id": cursor.lastrowid, "equipment_name": equipment_name, "status": status}