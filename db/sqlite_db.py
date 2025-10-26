"""
SQLite Database for structured data storage.
Handles users, goals, restrictions, preferences, meal plans, and tracking.
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os


class SQLiteDB:
    def __init__(self, db_path: str = "./data/nutrigenie.db"):
        """Initialize SQLite database connection."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.create_tables()
    
    def create_tables(self):
        """Create all necessary tables."""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER,
                sex TEXT,
                height REAL,
                weight REAL,
                country TEXT,
                ethnicity TEXT,
                activity_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_goals (
                goal_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                target_weight REAL,
                target_timeline_weeks INTEGER,
                daily_calories INTEGER,
                protein_g INTEGER,
                carbs_g INTEGER,
                fats_g INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # User restrictions (allergies, medical conditions, religious)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_restrictions (
                restriction_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                restriction TEXT NOT NULL,
                severity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # User preferences (diet type, cuisines, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                preference_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                diet_type TEXT,
                cuisine_preferences TEXT,
                meals_per_day INTEGER DEFAULT 3,
                cooking_time_max INTEGER,
                budget_weekly REAL,
                meal_complexity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Meal plans
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                plan_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                week_start_date DATE,
                status TEXT DEFAULT 'active',
                total_cost REAL,
                created_by_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Planned meals (original meal schedule)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planned_meals (
                meal_id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                day_of_week TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                recipe_name TEXT,
                calories INTEGER,
                protein_g REAL,
                carbs_g REAL,
                fats_g REAL,
                prep_time_min INTEGER,
                ingredients TEXT,
                is_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES meal_plans(plan_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Actual meals (what user actually ate)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actual_meals (
                actual_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                plan_id TEXT,
                planned_meal_id TEXT,
                day_of_week TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                food_description TEXT,
                calories INTEGER,
                protein_g REAL,
                carbs_g REAL,
                fats_g REAL,
                is_planned BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logged_by_agent TEXT,
                FOREIGN KEY (plan_id) REFERENCES meal_plans(plan_id),
                FOREIGN KEY (planned_meal_id) REFERENCES planned_meals(meal_id)
            )
        """)
        
        # Meal modifications log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_modifications (
                mod_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                day_of_week TEXT NOT NULL,
                modification_type TEXT NOT NULL,
                original_calories INTEGER,
                new_calories INTEGER,
                reason TEXT,
                adjusted_by_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES meal_plans(plan_id)
            )
        """)
        
        # Daily macros tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_macros (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                plan_id TEXT,
                date DATE NOT NULL,
                planned_calories INTEGER,
                actual_calories INTEGER,
                planned_protein_g REAL,
                actual_protein_g REAL,
                planned_carbs_g REAL,
                actual_carbs_g REAL,
                planned_fats_g REAL,
                actual_fats_g REAL,
                adherence_score REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES meal_plans(plan_id)
            )
        """)
        
        self.conn.commit()
        print("✅ SQLite tables created successfully")
    
    # ============ USER OPERATIONS ============
    
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (user_id, name, email, age, sex, height, weight, country, ethnicity, activity_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            user_data.get('name'),
            user_data.get('email'),
            user_data.get('age'),
            user_data.get('sex'),
            user_data.get('height'),
            user_data.get('weight'),
            user_data.get('country'),
            user_data.get('ethnicity'),
            user_data.get('activity_level')
        ))
        
        self.conn.commit()
        return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_user(self, user_id: str, updates: Dict[str, Any]):
        """Update user information."""
        cursor = self.conn.cursor()
        updates['updated_at'] = datetime.now()
        
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [user_id]
        
        cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
        self.conn.commit()
    
    # ============ GOALS OPERATIONS ============
    
    def create_goal(self, user_id: str, goal_data: Dict[str, Any]) -> str:
        """Create a new goal for user."""
        goal_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_goals 
            (goal_id, user_id, goal_type, target_weight, target_timeline_weeks, 
             daily_calories, protein_g, carbs_g, fats_g)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal_id, user_id,
            goal_data.get('goal_type'),
            goal_data.get('target_weight'),
            goal_data.get('target_timeline_weeks'),
            goal_data.get('daily_calories'),
            goal_data.get('protein_g'),
            goal_data.get('carbs_g'),
            goal_data.get('fats_g')
        ))
        
        self.conn.commit()
        return goal_id
    
    def get_active_goals(self, user_id: str) -> List[Dict]:
        """Get active goals for user."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM user_goals 
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    # ============ RESTRICTIONS OPERATIONS ============
    
    def add_restriction(self, user_id: str, restriction_type: str, restriction: str, severity: str = "moderate") -> str:
        """Add a restriction (allergy, medical, religious)."""
        restriction_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_restrictions (restriction_id, user_id, type, restriction, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (restriction_id, user_id, restriction_type, restriction, severity))
        
        self.conn.commit()
        return restriction_id
    
    def get_restrictions(self, user_id: str) -> List[Dict]:
        """Get all restrictions for user."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM user_restrictions WHERE user_id = ?
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    # ============ PREFERENCES OPERATIONS ============
    
    def create_preferences(self, user_id: str, pref_data: Dict[str, Any]) -> str:
        """Create user preferences."""
        pref_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        # Convert lists to JSON strings
        cuisine_prefs = json.dumps(pref_data.get('cuisine_preferences', []))
        
        cursor.execute("""
            INSERT INTO user_preferences 
            (preference_id, user_id, diet_type, cuisine_preferences, meals_per_day, 
             cooking_time_max, budget_weekly, meal_complexity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pref_id, user_id,
            pref_data.get('diet_type'),
            cuisine_prefs,
            pref_data.get('meals_per_day', 3),
            pref_data.get('cooking_time_max'),
            pref_data.get('budget_weekly'),
            pref_data.get('meal_complexity', 'moderate')
        ))
        
        self.conn.commit()
        return pref_id
    
    def get_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user preferences."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM user_preferences WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            pref = dict(row)
            # Parse JSON fields
            pref['cuisine_preferences'] = json.loads(pref['cuisine_preferences'])
            return pref
        return None
    
    # ============ MEAL PLAN OPERATIONS ============
    
    def create_meal_plan(self, user_id: str, week_start_date: str, created_by_agent: str) -> str:
        """Create a new meal plan."""
        plan_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO meal_plans (plan_id, user_id, week_start_date, created_by_agent)
            VALUES (?, ?, ?, ?)
        """, (plan_id, user_id, week_start_date, created_by_agent))
        
        self.conn.commit()
        return plan_id
    
    def add_planned_meal(self, plan_id: str, user_id: str, meal_data: Dict[str, Any]) -> str:
        """Add a planned meal to a meal plan."""
        meal_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        ingredients_json = json.dumps(meal_data.get('ingredients', []))
        
        cursor.execute("""
            INSERT INTO planned_meals 
            (meal_id, plan_id, user_id, day_of_week, meal_type, recipe_name,
             calories, protein_g, carbs_g, fats_g, prep_time_min, ingredients)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meal_id, plan_id, user_id,
            meal_data.get('day_of_week'),
            meal_data.get('meal_type'),
            meal_data.get('recipe_name'),
            meal_data.get('calories'),
            meal_data.get('protein_g'),
            meal_data.get('carbs_g'),
            meal_data.get('fats_g'),
            meal_data.get('prep_time_min'),
            ingredients_json
        ))
        
        self.conn.commit()
        return meal_id
    
    def get_meal_plan(self, plan_id: str) -> Optional[Dict]:
        """Get meal plan with all meals."""
        cursor = self.conn.cursor()
        
        # Get plan metadata
        cursor.execute("SELECT * FROM meal_plans WHERE plan_id = ?", (plan_id,))
        plan = cursor.fetchone()
        if not plan:
            return None
        
        # Get all meals for this plan
        cursor.execute("""
            SELECT * FROM planned_meals 
            WHERE plan_id = ? 
            ORDER BY 
                CASE day_of_week
                    WHEN 'monday' THEN 1
                    WHEN 'tuesday' THEN 2
                    WHEN 'wednesday' THEN 3
                    WHEN 'thursday' THEN 4
                    WHEN 'friday' THEN 5
                    WHEN 'saturday' THEN 6
                    WHEN 'sunday' THEN 7
                END,
                CASE meal_type
                    WHEN 'breakfast' THEN 1
                    WHEN 'lunch' THEN 2
                    WHEN 'dinner' THEN 3
                    WHEN 'snack' THEN 4
                END
        """, (plan_id,))
        
        meals = [dict(row) for row in cursor.fetchall()]
        
        # Parse ingredients JSON
        for meal in meals:
            meal['ingredients'] = json.loads(meal['ingredients'])
        
        result = dict(plan)
        result['meals'] = meals
        return result
    
    def get_user_active_plan(self, user_id: str) -> Optional[Dict]:
        """Get user's active meal plan."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM meal_plans 
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        plan = cursor.fetchone()
        if plan:
            return self.get_meal_plan(dict(plan)['plan_id'])
        return None
    
    # ============ ACTUAL MEALS & MODIFICATIONS ============
    
    def log_actual_meal(self, user_id: str, meal_data: Dict[str, Any]) -> str:
        """Log what user actually ate."""
        actual_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO actual_meals 
            (actual_id, user_id, plan_id, planned_meal_id, day_of_week, meal_type,
             food_description, calories, protein_g, carbs_g, fats_g, is_planned, logged_by_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            actual_id,
            user_id,
            meal_data.get('plan_id'),
            meal_data.get('planned_meal_id'),
            meal_data.get('day_of_week'),
            meal_data.get('meal_type'),
            meal_data.get('food_description'),
            meal_data.get('calories'),
            meal_data.get('protein_g'),
            meal_data.get('carbs_g'),
            meal_data.get('fats_g'),
            meal_data.get('is_planned', False),
            meal_data.get('logged_by_agent')
        ))
        
        self.conn.commit()
        return actual_id
    
    def log_modification(self, user_id: str, plan_id: str, mod_data: Dict[str, Any]) -> str:
        """Log a meal plan modification."""
        mod_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO meal_modifications 
            (mod_id, user_id, plan_id, day_of_week, modification_type,
             original_calories, new_calories, reason, adjusted_by_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mod_id, user_id, plan_id,
            mod_data.get('day_of_week'),
            mod_data.get('modification_type'),
            mod_data.get('original_calories'),
            mod_data.get('new_calories'),
            mod_data.get('reason'),
            mod_data.get('adjusted_by_agent')
        ))
        
        self.conn.commit()
        return mod_id
    
    def clear_all_data(self):
        """Clear all data from all tables (useful for testing)."""
        cursor = self.conn.cursor()

        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Delete data from all tables in correct order (children first)
        tables = [
            'daily_macros',
            'meal_modifications',
            'actual_meals',
            'planned_meals',
            'meal_plans',
            'user_preferences',
            'user_restrictions',
            'user_goals',
            'users'
        ]

        for table in tables:
            cursor.execute(f"DELETE FROM {table}")

        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        self.conn.commit()
        print("✅ All database data cleared")

    def clear_user_data(self, user_id: str):
        """Clear all data for a specific user."""
        cursor = self.conn.cursor()

        # Delete in correct order (children first)
        cursor.execute("DELETE FROM daily_macros WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM meal_modifications WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM actual_meals WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM planned_meals WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM meal_plans WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_restrictions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_goals WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

        self.conn.commit()
        print(f"✅ Cleared all data for user: {user_id}")

    def delete_user_by_email(self, email: str):
        """Delete user by email (useful for test cleanup)."""
        cursor = self.conn.cursor()

        # Find user_id by email
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()

        if row:
            user_id = dict(row)['user_id']
            self.clear_user_data(user_id)
            print(f"✅ Deleted user with email: {email}")
        else:
            print(f"ℹ️  No user found with email: {email}")

    def close(self):
        """Close database connection."""
        self.conn.close()
