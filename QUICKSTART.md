# 🚀 NutriGenie - Quick Start Guide

## ⚡ Get Running in 5 Minutes

### Step 1: Add Your Claude API Key (1 min)

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your key
nano .env
```

Add this line:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Save and exit (Ctrl+X, Y, Enter)

---

### Step 2: Test Everything Works (1 min)

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python test_system.py
```

You should see:
```
✅ All tests passed successfully!
```

---

### Step 3: Start the Agent (1 min)

```bash
python first_agent.py
```

You should see:
```
🚀 Starting Nutrition Planner Agent...
🤖 Nutrition Planner Agent started!
Agent address: agent1q...
```

Keep this terminal open!

---

### Step 4: Open the Form (1 min)

In a new terminal:
```bash
open frontend/user_form.html
```

Or manually open `frontend/user_form.html` in your browser.

---

### Step 5: Fill Out the Form (1 min)

**Required fields:**
- Name
- Age
- Sex
- Height (cm)
- Weight (kg)
- Activity Level
- Primary Goal

**Optional but recommended:**
- Allergies
- Medical conditions
- Diet type
- Cuisine preferences
- Budget

Click "Generate My Meal Plan"

---

## 🎯 What Happens Next?

Currently, the form saves data to localStorage. To connect it to the agent:

### Option A: Manual Test (Quick)

```python
# In a Python shell
from first_agent import UserProfileRequest, nutrition_agent
from db.memory import get_memory

# Create test user data
user_data = {
    'name': 'Test User',
    'age': 30,
    'sex': 'male',
    'height': 175.0,
    'weight': 80.0,
    'activity_level': 'moderately_active',
    'goal_type': 'lose_weight',
    'target_weight': 70.0,
    'target_timeline_weeks': 12,
    'diet_type': 'omnivore',
    'allergies': ['peanuts'],
    'medical_conditions': [],
    'cuisine_preferences': ['italian', 'mexican'],
    'meals_per_day': 3,
    'cooking_time_max': 30,
    'budget_weekly': 100.0
}

# Get memory
memory = get_memory()

# Create profile and generate plan
user_id = memory.create_user_profile(user_data)
context = memory.get_user_context(user_id)

# View the plan
plan = memory.get_active_meal_plan(user_id)
print(f"Created plan with {len(plan['meals'])} meals")
```

### Option B: Build API Endpoint (Recommended)

Create `api_server.py`:

```python
from flask import Flask, request, jsonify
from first_agent import UserProfileRequest
from db.memory import get_memory
import asyncio

app = Flask(__name__)
memory = get_memory()

@app.route('/api/create-user', methods=['POST'])
def create_user():
    user_data = request.json
    
    # Create profile
    user_id = memory.create_user_profile(user_data)
    
    # Get meal plan
    plan = memory.get_active_meal_plan(user_id)
    
    return jsonify({
        'user_id': user_id,
        'plan_id': plan['plan_id'],
        'meal_plan': plan
    })

if __name__ == '__main__':
    app.run(port=5000)
```

Then update the form's JavaScript to call this endpoint.

---

## 📊 View Your Data

### SQLite Database

```bash
# Install sqlite3 browser (optional)
brew install sqlite-browser

# Or use command line
sqlite3 data/nutrigenie.db

# View users
SELECT * FROM users;

# View meal plans
SELECT * FROM meal_plans;

# Exit
.quit
```

### Chroma Database

```python
from db.chroma_db import ChromaDB

chroma = ChromaDB()

# View conversations
convs = chroma.collections['conversations'].get()
print(f"Total conversations: {len(convs['ids'])}")

# View feedback
feedback = chroma.collections['food_feedback'].get()
print(f"Total feedback: {len(feedback['ids'])}")
```

---

## 🐛 Troubleshooting

### "Module not found" error

```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall if needed
pip install -r requirements.txt
```

### "Database locked" error

```bash
# Close all Python processes
pkill python

# Delete and recreate
rm -rf data/
python test_system.py
```

### "Claude API error"

```bash
# Check your API key
cat .env | grep ANTHROPIC

# Test the key
python -c "import anthropic; print('API key loaded')"
```

### Agent won't start

```bash
# Check if port 8001 is in use
lsof -i :8001

# Kill the process if needed
kill -9 <PID>

# Try again
python first_agent.py
```

---

## 📚 Learn More

- **Setup Guide**: `README_SETUP.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Code Documentation**: Check inline comments in source files

---

## 🎯 Next Steps

1. ✅ Get the agent running
2. ✅ Test with the form
3. 🔄 Connect form → agent → display
4. 🎨 Build meal plan display page
5. 🤖 Add more agents (Grocery Scout, Diet Coach)

---

## 💡 Tips for Hackathon

### Time Management
- **Hour 1-2**: Get everything running, test thoroughly
- **Hour 3-4**: Build API endpoint and connect form
- **Hour 5-6**: Create meal plan display page
- **Hour 7-8**: Polish UI, prepare demo

### Demo Flow
1. Show the form (user input)
2. Submit and show loading
3. Display generated meal plan
4. Highlight AI features (Claude, semantic search)
5. Show database (memory persistence)
6. Explain agent architecture

### Impressive Features to Highlight
- 🧠 Hybrid database (SQL + Vector)
- 🤖 Fetch.ai autonomous agents
- 💾 Persistent memory across sessions
- 🛡️ Safety-first (allergy filtering)
- 🌍 Cultural awareness
- 📊 Smart macro calculation

---

## 🎉 You're Ready!

Everything is set up and tested. Now go build something amazing! 🚀

**Questions?** Check the other documentation files or review the code comments.

**Good luck with your hackathon! 🌟**
