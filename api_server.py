"""
API Server for NutriGenie
Connects the frontend form to the Nutrition Planner Agent
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db.memory import get_memory
from first_agent import calculate_macros, generate_meal_plan_with_claude
import asyncio
import os
from datetime import datetime

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Initialize memory
memory = get_memory()


@app.route('/')
def index():
    """Serve the user form."""
    return send_from_directory('frontend', 'user_form.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'NutriGenie API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/create-user', methods=['POST'])
def create_user_and_plan():
    """
    Create user profile and generate meal plan.
    This is the main endpoint that connects form → agent → database.
    """
    try:
        # Get user data from request
        user_data = request.json
        
        if not user_data:
            return jsonify({
                'status': 'error',
                'message': 'No user data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'age', 'sex', 'height', 'weight', 'activity_level', 'goal_type']
        missing_fields = [field for field in required_fields if field not in user_data]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Step 1: Calculate macros
        print(f"📊 Calculating macros for {user_data.get('name')}...")
        macros = calculate_macros(user_data, {
            'goal_type': user_data.get('goal_type', 'maintain')
        })
        
        # Add macros to user data
        user_data.update(macros)
        
        # Step 2: Create user profile in memory
        print(f"💾 Creating user profile...")
        user_id = memory.create_user_profile(user_data)
        print(f"✅ User created: {user_id}")
        
        # Step 3: Get user context
        print(f"🔍 Loading user context...")
        user_context = memory.get_user_context(user_id)
        
        # Step 4: Generate meal plan with Claude
        print(f"🍽️ Generating meal plan with Claude AI...")
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            meals = loop.run_until_complete(
                generate_meal_plan_with_claude(user_context, macros)
            )
        except Exception as e:
            # Check if it's a Claude API error
            if "Claude API failed" in str(e):
                return jsonify({
                    'status': 'error',
                    'message': 'Claude API is not working. Please check your API key and try again.',
                    'error_type': 'claude_api_error'
                }), 500
            else:
                raise e
        finally:
            loop.close()
        
        # Step 5: Save meal plan to memory
        print(f"💾 Saving meal plan...")
        week_start = datetime.now().strftime('%Y-%m-%d')
        plan_id = memory.create_meal_plan(
            user_id=user_id,
            week_start_date=week_start,
            meals=meals,
            created_by_agent="nutrition_planner"
        )
        
        # Step 6: Get complete meal plan
        meal_plan = memory.get_meal_plan(plan_id)
        
        print(f"✅ Meal plan created successfully! Plan ID: {plan_id}")
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': f'Meal plan created successfully with {len(meals)} meals',
            'user_id': user_id,
            'plan_id': plan_id,
            'macros': macros,
            'meal_plan': meal_plan
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile by ID."""
    try:
        user = memory.sql.get_user(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'user': user
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/meal-plan/<plan_id>', methods=['GET'])
def get_meal_plan(plan_id):
    """Get meal plan by ID."""
    try:
        meal_plan = memory.get_meal_plan(plan_id)
        if not meal_plan:
            return jsonify({
                'status': 'error',
                'message': 'Meal plan not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'meal_plan': meal_plan
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/user/<user_id>/active-plan', methods=['GET'])
def get_user_active_plan(user_id):
    """Get user's active meal plan."""
    try:
        meal_plan = memory.get_active_meal_plan(user_id)
        if not meal_plan:
            return jsonify({
                'status': 'error',
                'message': 'No active meal plan found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'meal_plan': meal_plan
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    print("🚀 Starting NutriGenie API Server...")
    print("📝 Form available at: http://localhost:5000")
    print("🔗 API endpoint: http://localhost:5000/api/create-user")
    print("💚 Health check: http://localhost:5000/api/health")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
