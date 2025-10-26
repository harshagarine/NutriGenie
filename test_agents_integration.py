"""
Test script to demonstrate integration between first_agent and second_agent.
Shows how to:
1. Generate a meal plan with first_agent
2. Extract ingredients and find products with second_agent
"""

import asyncio
from uagents import Agent, Bureau, Context, Model
from first_agent import UserProfileRequest, MealPlanResponse, nutrition_agent
from second_agent import IngredientListRequest, ProductSuggestionsResponse, product_finder_agent
from db.memory import get_memory
import json


# Create a test orchestrator agent
test_agent = Agent(
    name="test_orchestrator",
    seed="test_orchestrator_seed",
    port=8003,
    endpoint=["http://localhost:8003/submit"]
)


@test_agent.on_event("startup")
async def startup(ctx: Context):
    """Send test request to nutrition agent on startup."""
    ctx.logger.info("🧪 Test Orchestrator started")

    # Clear existing test user data to avoid UNIQUE constraint errors
    memory = get_memory()
    test_email = 'john@example.com'

    ctx.logger.info(f"🧹 Cleaning up previous test data for {test_email}...")
    memory.delete_user_by_email(test_email)

    ctx.logger.info("✅ Database cleanup complete")

    # Sample user data for testing
    sample_user_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'age': 30,
        'sex': 'male',
        'height': 175,  # cm
        'weight': 75,   # kg
        'country': 'USA',
        'ethnicity': 'Caucasian',
        'activity_level': 'moderately_active',

        # Goals
        'goal_type': 'maintain',
        'target_weight': 75,
        'target_timeline_weeks': 12,

        # Restrictions
        'allergies': ['peanuts'],
        'medical_conditions': [],
        'religious_restrictions': [],

        # Preferences
        'diet_type': 'omnivore',
        'cuisine_preferences': ['mediterranean', 'asian'],
        'meals_per_day': 3,
        'cooking_time_max': 30,
        'budget_weekly': 100,
        'meal_complexity': 'moderate',

        # Likes/Dislikes
        'food_likes': ['chicken', 'salmon', 'vegetables'],
        'food_dislikes': ['liver', 'anchovies']
    }

    ctx.logger.info("📤 Sending user profile to Nutrition Agent...")

    # Send request to nutrition agent
    await ctx.send(
        nutrition_agent.address,
        UserProfileRequest(user_data=sample_user_data)
    )


@test_agent.on_message(model=MealPlanResponse)
async def handle_meal_plan_response(ctx: Context, sender: str, msg: MealPlanResponse):
    """Handle meal plan response and forward to product finder."""
    ctx.logger.info(f"📥 Received meal plan response from Nutrition Agent")
    ctx.logger.info(f"Status: {msg.status}")
    ctx.logger.info(f"Message: {msg.message}")

    if msg.status == "success":
        ctx.logger.info(f"✅ Meal plan created successfully!")
        ctx.logger.info(f"Plan ID: {msg.plan_id}")
        ctx.logger.info(f"User ID: {msg.user_id}")

        # Pretty print meal plan summary
        if msg.meal_plan:
            meals = msg.meal_plan.get('meals', [])
            ctx.logger.info(f"\n📋 Meal Plan Summary ({len(meals)} meals):")

            # Group by day
            days = {}
            for meal in meals:
                day = meal.get('day_of_week', 'unknown')
                if day not in days:
                    days[day] = []
                days[day].append(meal)

            for day, day_meals in sorted(days.items()):
                ctx.logger.info(f"\n  {day.upper()}:")
                for meal in day_meals:
                    ctx.logger.info(f"    • {meal.get('meal_type')}: {meal.get('recipe_name')}")
                    ctx.logger.info(f"      Ingredients: {', '.join(meal.get('ingredients', []))}")

        # Now send to product finder agent
        ctx.logger.info("\n📤 Sending ingredient list to Product Finder Agent...")
        await ctx.send(
            product_finder_agent.address,
            IngredientListRequest(
                plan_id=msg.plan_id,
                user_id=msg.user_id
            )
        )
    else:
        ctx.logger.error(f"❌ Meal plan creation failed: {msg.message}")


@test_agent.on_message(model=ProductSuggestionsResponse)
async def handle_product_suggestions(ctx: Context, sender: str, msg: ProductSuggestionsResponse):
    """Handle product suggestions response."""
    ctx.logger.info(f"\n📥 Received product suggestions from Product Finder Agent")
    ctx.logger.info(f"Status: {msg.status}")
    ctx.logger.info(f"Message: {msg.message}")

    if msg.status == "success" and msg.suggestions:
        ctx.logger.info(f"\n🛒 Product Suggestions:\n")

        for suggestion in msg.suggestions:
            ingredient = suggestion['ingredient']
            products = suggestion['products']

            ctx.logger.info(f"{'='*60}")
            ctx.logger.info(f"Ingredient: {ingredient.upper()}")
            ctx.logger.info(f"{'='*60}")

            if products:
                for i, product in enumerate(products, 1):
                    ctx.logger.info(f"\n  {i}. {product['product_name']}")
                    ctx.logger.info(f"     Brand: {product['brand']}")
                    ctx.logger.info(f"     Nutri-Score: {product['nutri_score']}")
                    ctx.logger.info(f"     Per 100g: {product['calories_per_100g']}kcal | "
                                  f"Protein: {product['protein_per_100g']}g | "
                                  f"Carbs: {product['carbs_per_100g']}g | "
                                  f"Fats: {product['fats_per_100g']}g")
                    if product.get('product_url'):
                        ctx.logger.info(f"     URL: {product['product_url']}")
            else:
                ctx.logger.info(f"  ⚠️  No products found for this ingredient")

            ctx.logger.info("")  # Empty line for readability

        ctx.logger.info(f"\n{'='*60}")
        ctx.logger.info("✅ Product suggestions complete!")
        ctx.logger.info(f"{'='*60}\n")
    else:
        ctx.logger.warning(f"⚠️ No product suggestions available")


@test_agent.on_interval(period=120.0)
async def periodic_log(ctx: Context):
    """Periodic log."""
    ctx.logger.info("🧪 Test orchestrator is running...")


if __name__ == "__main__":
    import signal
    import sys

    print("🚀 Starting Test Integration...")
    print("\nThis script will:")
    print("1. Create a sample user profile")
    print("2. Generate a 7-day meal plan with first_agent")
    print("3. Extract ingredients and find products with second_agent")
    print("4. Display product suggestions for each ingredient")
    print("\n" + "="*60 + "\n")

    # Create bureau to run all agents together
    bureau = Bureau(port=8000, endpoint="http://localhost:8000/submit")

    # Add all agents to the bureau
    bureau.add(test_agent)
    bureau.add(nutrition_agent)
    bureau.add(product_finder_agent)

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down agents...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Run the bureau
    try:
        bureau.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(0)
