import sqlite3
import hashlib
import json
import os

class UserDatabase:
    def __init__(self, db_path="data/users/users.db"):
        self.db_path = db_path
        # Ensure the directory exists before connecting
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.create_tables()

    def _get_connection(self):
        """Helper method to get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def create_tables(self):
        """Creates the database and the users table if it doesn't exist."""
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_locked BOOLEAN DEFAULT 0,
            budget TEXT DEFAULT '{}',
            tasks TEXT DEFAULT '[]',
            contacts TEXT DEFAULT '[]',
            grades TEXT DEFAULT '[]',
            journal TEXT DEFAULT '[]'
        );
        """
        with self._get_connection() as conn:
            conn.execute(schema)
            conn.commit()

    def add_user(self, username, password, is_locked=False):
        """Adds a new user to the database."""
        username = username.lower()
        
        # Hash the password (highly recommended to hash ALL passwords)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Default empty JSON structures for new users
        default_dict = json.dumps({})
        default_list = json.dumps([])

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """INSERT INTO users (username, password, is_locked, budget, tasks, contacts, grades, journal) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (username, hashed_password, is_locked, default_dict, default_list, default_list, default_list, default_list)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"User '{username}' already exists. ❌")
            return False

    def remove_user(self, username):
        """Deletes a user from the database."""
        username = username.lower()
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return cursor.rowcount > 0 # Returns True if a user was actually deleted

    def get_user_data(self, username):
        """Fetches all data for a specific user and parses JSON fields."""
        username = username.lower()
        with self._get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user:
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "password": user["password"],
                "is_locked": bool(user["is_locked"]),
                "budget": json.loads(user["budget"]),
                "tasks": json.loads(user["tasks"]),
                "contacts": json.loads(user["contacts"]),
                "grades": json.loads(user["grades"]),
                "journal": json.loads(user["journal"])
            }
        return None

    def verify_login(self, username, password):
        """Checks credentials and returns user data if successful."""
        user = self.get_user_data(username)
        if not user:
            return None
            
        hashed_attempt = hashlib.sha256(password.encode()).hexdigest()
        
        # Note: Adapted from your logic. 
        # If locked, checks plain text (legacy logic). If unlocked, checks hash.
        if user["is_locked"] and user["password"] == password:
            return user
        elif not user["is_locked"] and user["password"] == hashed_attempt:
            return user
            
        return None

    def update_user_field(self, username, field_name, data):
        """
        Updates a specific JSON field (like tasks or budget) for a user.
        Example: db.update_user_field("john", "tasks", [{"title": "Buy milk"}])
        """
        allowed_fields = ["budget", "tasks", "contacts", "grades", "journal", "is_locked"]
        if field_name not in allowed_fields:
            raise ValueError(f"Field '{field_name}' cannot be updated this way.")

        # Convert lists/dicts back to JSON strings before saving, unless it's a boolean (is_locked)
        if field_name != "is_locked":
            data = json.dumps(data)

        username = username.lower()
        with self._get_connection() as conn:
            # Safe string formatting here because we already validated field_name against allowed_fields
            conn.execute(f"UPDATE users SET {field_name} = ? WHERE username = ?", (data, username))
            conn.commit()