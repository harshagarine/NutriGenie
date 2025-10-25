"""
Nutrition Planner Agent - First Agent
Uses Fetch.ai uAgents to create personalized meal plans.
"""

from uagents import Agent, Context, Model
from db.memory import get_memory
from typing import Dict, List, Any, Optional
import anthropic
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

load_dotenv()

# Initialize memory
memory = get_memory()

# Initialize Claude API
claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Define message models
class UserProfileRequest(Model):
    """Request to create user profile and generate meal plan."""
    user_data: dict

class MealPlanResponse(Model):
    """Response containing generated meal plan."""
    user_id: str
    plan_id: str
    status: str
    message: str
    meal_plan: Optional[dict] = None


# Create the Nutrition Planner Agent
nutrition_agent = Agent(
    name="nutrition_planner",
    seed="nutrition_planner_seed_phrase_nutrigenie",
    port=8001,
    endpoint=["http://localhost:8001/submit"]
)


@nutrition_agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event."""
    ctx.logger.info(f"🤖 Nutrition Planner Agent started!")
    ctx.logger.info(f"Agent address: {nutrition_agent.address}")


def calculate_macros(user_data: Dict[str, Any], goals: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate daily macros based on user data and goals.
    Uses Mifflin-St Jeor equation for BMR and activity multipliers for TDEE.
    """
    # BMR calculation (Mifflin-St Jeor)
    weight = user_data['weight']
    height = user_data['height']
    age = user_data['age']
    sex = user_data['sex']
    
    if sex == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    # TDEE calculation (activity multiplier)
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extremely_active': 1.9
    }
    
    activity_level = user_data.get('activity_level', 'moderately_active')
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)
    
    # Adjust for goals
    goal_type = goals.get('goal_type', 'maintain')
    
    if goal_type == 'lose_weight':
        daily_calories = int(tdee - 500)  # 500 cal deficit
        protein_ratio = 0.40
        carbs_ratio = 0.30
        fats_ratio = 0.30
    elif goal_type == 'gain_muscle':
        daily_calories = int(tdee + 300)  # 300 cal surplus
        protein_ratio = 0.30
        carbs_ratio = 0.40
        fats_ratio = 0.30
    elif goal_type == 'bulk':
        daily_calories = int(tdee + 500)  # 500 cal surplus
        protein_ratio = 0.25
        carbs_ratio = 0.45
        fats_ratio = 0.30
    elif goal_type == 'cut':
        daily_calories = int(tdee - 300)  # 300 cal deficit
        protein_ratio = 0.40
        carbs_ratio = 0.30
        fats_ratio = 0.30
    else:  # maintain
        daily_calories = int(tdee)
        protein_ratio = 0.30
        carbs_ratio = 0.40
        fats_ratio = 0.30
    
    # Calculate macro grams
    protein_g = int((daily_calories * protein_ratio) / 4)  # 4 cal per gram
    carbs_g = int((daily_calories * carbs_ratio) / 4)  # 4 cal per gram
    fats_g = int((daily_calories * fats_ratio) / 9)  # 9 cal per gram
    
    return {
        'daily_calories': daily_calories,
        'protein_g': protein_g,
        'carbs_g': carbs_g,
        'fats_g': fats_g
    }


async def generate_meal_plan_with_claude(
    user_context: Dict[str, Any],
    macros: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    Use Claude to generate a personalized 7-day meal plan.
    """
    user = user_context['user']
    restrictions = user_context['restrictions']
    preferences = user_context['preferences']
    
    # Build restrictions list
    allergies = [r['restriction'] for r in restrictions if r['type'] == 'allergy']
    medical = [r['restriction'] for r in restrictions if r['type'] == 'medical']
    
    # Build prompt
    prompt = f"""You are a professional nutritionist creating a personalized 7-day meal plan.

USER PROFILE:
- Age: {user['age']}, Sex: {user['sex']}
- Current Weight: {user['weight']}kg, Height: {user['height']}cm
- Country: {user.get('country', 'Not specified')}
- Ethnicity: {user.get('ethnicity', 'Not specified')}
- Goal: {user_context['goals'][0]['goal_type'] if user_context['goals'] else 'maintain'}

DAILY TARGETS:
- Calories: {macros['daily_calories']} kcal
- Protein: {macros['protein_g']}g
- Carbs: {macros['carbs_g']}g
- Fats: {macros['fats_g']}g

RESTRICTIONS (CRITICAL - MUST AVOID):
- Allergies: {', '.join(allergies) if allergies else 'None'}
- Medical Conditions: {', '.join(medical) if medical else 'None'}

PREFERENCES:
- Diet Type: {preferences.get('diet_type', 'omnivore')}
- Cuisines: {', '.join(preferences.get('cuisine_preferences', [])) if preferences.get('cuisine_preferences') else 'Any'}
- Meals Per Day: {preferences.get('meals_per_day', 3)}
- Max Cooking Time Per Meal: {preferences.get('cooking_time_max', 30)} minutes
- Budget: ${preferences.get('budget_weekly', 100)}/week

Create a 7-day meal plan (Monday-Sunday) with {preferences.get('meals_per_day', 3)} meals per day.

For each meal, provide:
1. Recipe name
2. Estimated calories, protein, carbs, fats
3. Prep time in minutes
4. List of main ingredients (5-7 items)

Return ONLY a valid JSON array with this structure:
[
  {{
    "day_of_week": "monday",
    "meal_type": "breakfast",
    "recipe_name": "Greek Yogurt Parfait",
    "calories": 350,
    "protein_g": 25,
    "carbs_g": 40,
    "fats_g": 10,
    "prep_time_min": 10,
    "ingredients": ["greek yogurt", "berries", "granola", "honey", "almonds"]
  }},
  ...
]

IMPORTANT:
- Ensure total daily calories are close to {macros['daily_calories']} kcal
- Strictly avoid all allergens: {', '.join(allergies) if allergies else 'None'}
- Respect dietary restrictions: {preferences.get('diet_type', 'omnivore')}
- Keep prep times under {preferences.get('cooking_time_max', 30)} minutes PER MEAL
- Provide variety across the week
- Return ONLY valid JSON, no other text"""

    try:
        response = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",  # Claude Haiku 3.5 (available in your account)
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract JSON from response
        content = response.content[0].text
        
        # Try to parse JSON
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        meals = json.loads(content)
        return meals
        
    except Exception as e:
        error_msg = f"Claude API failed: {str(e)}"
        print(error_msg)
        # Raise exception so agent can handle it properly
        raise Exception(error_msg)


@nutrition_agent.on_message(model=UserProfileRequest)
async def handle_user_profile(ctx: Context, sender: str, msg: UserProfileRequest):
    """
    Handle user profile creation and meal plan generation.
    This is the main workflow for the Nutrition Planner Agent.
    """
    ctx.logger.info(f"📥 Received user profile request from {sender}")
    
    try:
        user_data = msg.user_data
        
        # Step 1: Calculate macros
        ctx.logger.info("🧮 Calculating macros...")
        macros = calculate_macros(user_data, {
            'goal_type': user_data.get('goal_type', 'maintain')
        })
        
        # Add macros to user data
        user_data.update(macros)
        
        # Step 2: Create user profile in memory
        ctx.logger.info("💾 Creating user profile in memory...")
        user_id = memory.create_user_profile(user_data)
        
        # Step 3: Get user context from memory
        ctx.logger.info("🔍 Loading user context...")
        user_context = memory.get_user_context(user_id)
        
        # Step 4: Generate meal plan with Claude
        ctx.logger.info("🍽️ Generating meal plan with Claude AI...")
        meals = await generate_meal_plan_with_claude(user_context, macros)
        
        # Step 5: Save meal plan to memory
        ctx.logger.info("💾 Saving meal plan to memory...")
        week_start = datetime.now().strftime('%Y-%m-%d')
        plan_id = memory.create_meal_plan(
            user_id=user_id,
            week_start_date=week_start,
            meals=meals,
            created_by_agent="nutrition_planner"
        )
        
        # Step 6: Get complete meal plan
        meal_plan = memory.get_meal_plan(plan_id)
        
        ctx.logger.info(f"✅ Meal plan created successfully! Plan ID: {plan_id}")
        
        # Send response
        response = MealPlanResponse(
            user_id=user_id,
            plan_id=plan_id,
            status="success",
            message=f"Meal plan created successfully with {len(meals)} meals",
            meal_plan=meal_plan
        )
        
        await ctx.send(sender, response)
        
    except Exception as e:
        error_message = str(e)
        
        # Check if it's a Claude API failure
        if "Claude API failed" in error_message:
            ctx.logger.error(f"❌ Claude API is not working: {e}")
            response = MealPlanResponse(
                user_id="",
                plan_id="",
                status="error",
                message="Claude API is not working. Please check your API key and try again."
            )
        else:
            ctx.logger.error(f"❌ Error creating meal plan: {e}")
            response = MealPlanResponse(
                user_id="",
                plan_id="",
                status="error",
                message=f"Error: {error_message}"
            )
        
        await ctx.send(sender, response)


@nutrition_agent.on_interval(period=60.0)
async def log_status(ctx: Context):
    """Periodic status log."""
    ctx.logger.info("🤖 Nutrition Planner Agent is running...")


if __name__ == "__main__":
    print("🚀 Starting Nutrition Planner Agent...")
    print(f"Agent Address: {nutrition_agent.address}")
    nutrition_agent.run()
