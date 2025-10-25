"""
Test script to verify database and agent integration.
"""

from db.memory import get_memory
import json

def test_database():
    """Test database creation and basic operations."""
    print("=" * 60)
    print("🧪 Testing NutriGenie Database System")
    print("=" * 60)
    
    # Initialize memory
    memory = get_memory()
    
    # Test user data
    test_user = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'age': 30,
        'sex': 'male',
        'height': 175.0,
        'weight': 80.0,
        'country': 'USA',
        'ethnicity': 'Caucasian',
        'activity_level': 'moderately_active',
        'goal_type': 'lose_weight',
        'target_weight': 70.0,
        'target_timeline_weeks': 12,
        'daily_calories': 2000,
        'protein_g': 150,
        'carbs_g': 200,
        'fats_g': 67,
        'allergies': ['peanuts', 'shellfish'],
        'medical_conditions': ['hypertension'],
        'religious_restrictions': [],
        'diet_type': 'omnivore',
        'cuisine_preferences': ['italian', 'mexican', 'asian'],
        'meals_per_day': 3,
        'cooking_time_max': 30,
        'budget_weekly': 100.0,
        'meal_complexity': 'moderate',
        'food_likes': ['spicy food', 'grilled chicken', 'fresh vegetables'],
        'food_dislikes': ['mushy textures', 'overly sweet desserts']
    }
    
    print("\n1️⃣ Creating user profile...")
    user_id = memory.create_user_profile(test_user)
    print(f"   ✅ User created with ID: {user_id}")
    
    print("\n2️⃣ Retrieving user context...")
    context = memory.get_user_context(user_id)
    print(f"   ✅ User: {context['user']['name']}, {context['user']['age']} years old")
    print(f"   ✅ Goals: {len(context['goals'])} active goal(s)")
    print(f"   ✅ Restrictions: {len(context['restrictions'])} restriction(s)")
    print(f"   ✅ Preferences: Diet type = {context['preferences']['diet_type']}")
    
    print("\n3️⃣ Testing safety restrictions...")
    safety = memory.get_safety_restrictions(user_id)
    print(f"   ✅ Critical restrictions: {', '.join(safety)}")
    
    print("\n4️⃣ Testing macro calculation...")
    macros = memory.calculate_daily_macros(user_id)
    print(f"   ✅ Daily calories: {macros['calories']} kcal")
    print(f"   ✅ Protein: {macros['protein_g']}g")
    print(f"   ✅ Carbs: {macros['carbs_g']}g")
    print(f"   ✅ Fats: {macros['fats_g']}g")
    
    print("\n5️⃣ Creating test meal plan...")
    test_meals = [
        {
            'day_of_week': 'monday',
            'meal_type': 'breakfast',
            'recipe_name': 'Greek Yogurt Parfait',
            'calories': 350,
            'protein_g': 25.0,
            'carbs_g': 40.0,
            'fats_g': 10.0,
            'prep_time_min': 10,
            'ingredients': ['greek yogurt', 'berries', 'granola', 'honey']
        },
        {
            'day_of_week': 'monday',
            'meal_type': 'lunch',
            'recipe_name': 'Grilled Chicken Salad',
            'calories': 450,
            'protein_g': 40.0,
            'carbs_g': 30.0,
            'fats_g': 20.0,
            'prep_time_min': 20,
            'ingredients': ['chicken breast', 'mixed greens', 'tomatoes', 'olive oil']
        }
    ]
    
    plan_id = memory.create_meal_plan(
        user_id=user_id,
        week_start_date='2025-10-28',
        meals=test_meals,
        created_by_agent='test_script'
    )
    print(f"   ✅ Meal plan created with ID: {plan_id}")
    
    print("\n6️⃣ Retrieving meal plan...")
    meal_plan = memory.get_meal_plan(plan_id)
    print(f"   ✅ Plan has {len(meal_plan['meals'])} meals")
    for meal in meal_plan['meals']:
        print(f"      - {meal['day_of_week'].capitalize()} {meal['meal_type']}: {meal['recipe_name']} ({meal['calories']} cal)")
    
    print("\n7️⃣ Testing conversation memory...")
    conv_id = memory.save_conversation(
        user_id=user_id,
        agent='nutrition_planner',
        role='user',
        message='I really love spicy food and grilled chicken'
    )
    print(f"   ✅ Conversation saved with ID: {conv_id}")
    
    print("\n8️⃣ Searching conversation context...")
    results = memory.search_conversation_context(
        user_id=user_id,
        query='food preferences'
    )
    print(f"   ✅ Found {len(results)} relevant conversations")
    
    print("\n9️⃣ Testing food feedback...")
    feedback_id = memory.save_meal_feedback(
        user_id=user_id,
        meal_id=meal_plan['meals'][0]['meal_id'],
        food_description='Greek Yogurt Parfait',
        rating=5,
        feedback_text='Loved it! Perfect amount of sweetness and very filling',
        cuisine='mediterranean'
    )
    print(f"   ✅ Feedback saved with ID: {feedback_id}")
    
    print("\n10️⃣ Testing food preferences context...")
    food_prefs = memory.get_food_preferences_context(user_id)
    print(f"   ✅ Liked foods: {len(food_prefs['liked_foods'])} items")
    print(f"   ✅ Disliked foods: {len(food_prefs['disliked_foods'])} items")
    print(f"   ✅ Preferences: {len(food_prefs['preferences'])} items")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed successfully!")
    print("=" * 60)
    
    print(f"\n📊 Test Summary:")
    print(f"   User ID: {user_id}")
    print(f"   Plan ID: {plan_id}")
    print(f"   Database: SQLite + Chroma")
    print(f"   Status: Ready for agent integration")
    
    # Close memory
    memory.close()


if __name__ == "__main__":
    test_database()
