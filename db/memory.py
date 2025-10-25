"""
Unified Memory Layer - Single interface for agents to access both databases.
Agents should always use this layer instead of directly accessing SQLite or Chroma.
"""

from typing import Dict, List, Optional, Any
from .sqlite_db import SQLiteDB
from .chroma_db import ChromaDB
import os
from dotenv import load_dotenv

load_dotenv()


class Memory:
    """
    Unified memory interface for all agents.
    Combines structured data (SQLite) and semantic memory (Chroma).
    """
    
    def __init__(
        self,
        sqlite_path: Optional[str] = None,
        chroma_path: Optional[str] = None
    ):
        """Initialize both databases."""
        sqlite_path = sqlite_path or os.getenv('SQLITE_DB_PATH', './data/nutrigenie.db')
        chroma_path = chroma_path or os.getenv('CHROMA_DB_PATH', './data/chroma_db')
        
        self.sql = SQLiteDB(sqlite_path)
        self.vector = ChromaDB(chroma_path)
        
        print("✅ Memory layer initialized with SQLite + Chroma")
    
    # ============ USER PROFILE OPERATIONS ============
    
    def create_user_profile(self, user_data: Dict[str, Any]) -> str:
        """
        Create complete user profile from form data.
        Stores structured data in SQL and semantic preferences in Chroma.
        """
        # 1. Create user in SQLite
        user_id = self.sql.create_user({
            'name': user_data.get('name'),
            'email': user_data.get('email'),
            'age': user_data.get('age'),
            'sex': user_data.get('sex'),
            'height': user_data.get('height'),
            'weight': user_data.get('weight'),
            'country': user_data.get('country'),
            'ethnicity': user_data.get('ethnicity'),
            'activity_level': user_data.get('activity_level')
        })
        
        # 2. Create goals
        if 'goal_type' in user_data:
            self.sql.create_goal(user_id, {
                'goal_type': user_data.get('goal_type'),
                'target_weight': user_data.get('target_weight'),
                'target_timeline_weeks': user_data.get('target_timeline_weeks'),
                'daily_calories': user_data.get('daily_calories'),
                'protein_g': user_data.get('protein_g'),
                'carbs_g': user_data.get('carbs_g'),
                'fats_g': user_data.get('fats_g')
            })
        
        # 3. Add restrictions (allergies, medical, religious)
        if 'allergies' in user_data and user_data['allergies']:
            for allergy in user_data['allergies']:
                self.sql.add_restriction(user_id, 'allergy', allergy, 'critical')
        
        if 'medical_conditions' in user_data and user_data['medical_conditions']:
            for condition in user_data['medical_conditions']:
                self.sql.add_restriction(user_id, 'medical', condition, 'important')
        
        if 'religious_restrictions' in user_data and user_data['religious_restrictions']:
            for restriction in user_data['religious_restrictions']:
                self.sql.add_restriction(user_id, 'religious', restriction, 'important')
        
        # 4. Create preferences
        if 'diet_type' in user_data:
            self.sql.create_preferences(user_id, {
                'diet_type': user_data.get('diet_type'),
                'cuisine_preferences': user_data.get('cuisine_preferences', []),
                'meals_per_day': user_data.get('meals_per_day', 3),
                'cooking_time_max': user_data.get('cooking_time_max'),
                'budget_weekly': user_data.get('budget_weekly'),
                'meal_complexity': user_data.get('meal_complexity', 'moderate')
            })
        
        # 5. Add semantic preferences to Chroma
        if 'food_likes' in user_data and user_data['food_likes']:
            for like in user_data['food_likes']:
                self.vector.add_preference(user_id, like, 'like', 'strong')
        
        if 'food_dislikes' in user_data and user_data['food_dislikes']:
            for dislike in user_data['food_dislikes']:
                self.vector.add_preference(user_id, dislike, 'dislike', 'strong')
        
        print(f"✅ Created user profile: {user_id}")
        return user_id
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user context for agents.
        Combines structured data from SQL and semantic context from Chroma.
        """
        context = {
            'user': self.sql.get_user(user_id),
            'goals': self.sql.get_active_goals(user_id),
            'restrictions': self.sql.get_restrictions(user_id),
            'preferences': self.sql.get_preferences(user_id),
            'semantic_preferences': self.vector.get_all_preferences(user_id),
            'recent_conversations': self.vector.get_recent_conversations(user_id, n_results=5),
            'food_feedback': self.vector.get_all_feedback(user_id)
        }
        
        return context
    
    # ============ CONVERSATION OPERATIONS ============
    
    def save_conversation(
        self,
        user_id: str,
        agent: str,
        role: str,
        message: str,
        session_id: Optional[str] = None
    ) -> str:
        """Save a conversation message."""
        return self.vector.add_conversation(user_id, agent, role, message, session_id)
    
    def search_conversation_context(
        self,
        user_id: str,
        query: str,
        agent: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """Search conversation history for relevant context."""
        return self.vector.search_conversations(user_id, query, n_results, agent)
    
    # ============ MEAL PLAN OPERATIONS ============
    
    def create_meal_plan(
        self,
        user_id: str,
        week_start_date: str,
        meals: List[Dict[str, Any]],
        created_by_agent: str
    ) -> str:
        """
        Create a complete meal plan with all meals.
        """
        # Create plan
        plan_id = self.sql.create_meal_plan(user_id, week_start_date, created_by_agent)
        
        # Add all meals
        for meal in meals:
            self.sql.add_planned_meal(plan_id, user_id, meal)
        
        # Log in conversation history
        self.vector.add_conversation(
            user_id,
            created_by_agent,
            'agent',
            f"Created meal plan for week starting {week_start_date}",
            session_id=plan_id
        )
        
        print(f"✅ Created meal plan: {plan_id} with {len(meals)} meals")
        return plan_id
    
    def get_active_meal_plan(self, user_id: str) -> Optional[Dict]:
        """Get user's active meal plan."""
        return self.sql.get_user_active_plan(user_id)
    
    def get_meal_plan(self, plan_id: str) -> Optional[Dict]:
        """Get specific meal plan."""
        return self.sql.get_meal_plan(plan_id)
    
    # ============ MEAL TRACKING & MODIFICATIONS ============
    
    def log_actual_meal(
        self,
        user_id: str,
        meal_data: Dict[str, Any],
        logged_by_agent: str
    ) -> str:
        """Log what user actually ate."""
        meal_data['logged_by_agent'] = logged_by_agent
        actual_id = self.sql.log_actual_meal(user_id, meal_data)
        
        # Also save to conversation
        self.vector.add_conversation(
            user_id,
            logged_by_agent,
            'user',
            f"Ate: {meal_data.get('food_description')} ({meal_data.get('calories')} cal)"
        )
        
        return actual_id
    
    def modify_meal_plan(
        self,
        user_id: str,
        plan_id: str,
        modification_data: Dict[str, Any],
        adjusted_by_agent: str
    ) -> str:
        """Log a meal plan modification."""
        modification_data['adjusted_by_agent'] = adjusted_by_agent
        mod_id = self.sql.log_modification(user_id, plan_id, modification_data)
        
        # Save context to Chroma
        self.vector.add_conversation(
            user_id,
            adjusted_by_agent,
            'agent',
            f"Modified meal plan: {modification_data.get('reason')}"
        )
        
        return mod_id
    
    # ============ FEEDBACK OPERATIONS ============
    
    def save_meal_feedback(
        self,
        user_id: str,
        meal_id: Optional[str],
        food_description: str,
        rating: int,
        feedback_text: str,
        cuisine: Optional[str] = None
    ) -> str:
        """Save user feedback on a meal."""
        return self.vector.add_food_feedback(
            user_id,
            meal_id,
            food_description,
            rating,
            feedback_text,
            cuisine
        )
    
    def get_food_preferences_context(
        self,
        user_id: str,
        query: str = "food preferences"
    ) -> Dict[str, List[Dict]]:
        """Get semantic food preferences for meal planning."""
        return {
            'liked_foods': self.vector.search_liked_foods(user_id, query, min_rating=4),
            'disliked_foods': self.vector.search_disliked_foods(user_id, query, max_rating=2),
            'preferences': self.vector.search_preferences(user_id, query)
        }
    
    # ============ AGENT HELPER METHODS ============
    
    def get_safety_restrictions(self, user_id: str) -> List[str]:
        """Get critical restrictions (allergies, medical) for safety checks."""
        restrictions = self.sql.get_restrictions(user_id)
        critical = [
            r['restriction'] 
            for r in restrictions 
            if r['severity'] in ['critical', 'important']
        ]
        return critical
    
    def calculate_daily_macros(self, user_id: str) -> Dict[str, int]:
        """Get target daily macros for user."""
        goals = self.sql.get_active_goals(user_id)
        if goals:
            goal = goals[0]
            return {
                'calories': goal['daily_calories'],
                'protein_g': goal['protein_g'],
                'carbs_g': goal['carbs_g'],
                'fats_g': goal['fats_g']
            }
        return {}
    
    def close(self):
        """Close all database connections."""
        self.sql.close()
        print("✅ Memory layer closed")


# Global memory instance (singleton pattern)
_memory_instance = None

def get_memory() -> Memory:
    """Get global memory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = Memory()
    return _memory_instance
