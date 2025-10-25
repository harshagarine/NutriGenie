# 🚀 NutriGenie - Running Guide

## ✅ Complete Flow Connected!

**Form → API → Agent → Database → Display**

---

## 🎯 Quick Start (3 Steps)

### Step 1: Add Your Claude API Key

```bash
# Create .env file (if not already done)
cp .env.example .env

# Edit and add your key
nano .env
```

Add:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 2: Start the API Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python api_server.py
```

You should see:
```
🚀 Starting NutriGenie API Server...
📝 Form available at: http://localhost:5000
🔗 API endpoint: http://localhost:5000/api/create-user
💚 Health check: http://localhost:5000/api/health
 * Running on http://0.0.0.0:5000
```

### Step 3: Open the Form

Open your browser and go to:
```
http://localhost:5000
```

Or manually open:
```bash
open http://localhost:5000
```

---

## 📋 Complete User Flow

### 1. Fill Out the Form
- **Required**: Name, Age, Sex, Height, Weight, Activity Level, Goal
- **Optional**: Email, Country, Ethnicity, Allergies, Medical Conditions, Diet Preferences
- Click **"🚀 Generate My Meal Plan"**

### 2. Wait for Generation
- Button changes to **"⏳ Generating Meal Plan..."**
- Backend calls Claude API
- Typically takes 10-30 seconds

### 3. View Results
- Success message shows:
  - User ID
  - Plan ID
  - Total meals
  - Daily macros
- Click **"📋 View Your Meal Plan"**

### 4. See Your Meal Plan
- 7-day calendar view
- Each day shows:
  - Breakfast, Lunch, Dinner (+ snacks if selected)
  - Calories and macros per meal
  - Prep time
  - Ingredients
- Daily totals for each day
- Download option available

---

## 🔍 API Endpoints

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Create User & Generate Plan
```bash
curl -X POST http://localhost:5000/api/create-user \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 30,
    "sex": "male",
    "height": 175,
    "weight": 80,
    "activity_level": "moderately_active",
    "goal_type": "lose_weight",
    "diet_type": "omnivore",
    "meals_per_day": 3,
    "cooking_time_max": 30,
    "allergies": ["peanuts"],
    "medical_conditions": [],
    "cuisine_preferences": ["italian", "mexican"]
  }'
```

### Get User's Active Plan
```bash
curl http://localhost:5000/api/user/{user_id}/active-plan
```

### Get Specific Meal Plan
```bash
curl http://localhost:5000/api/meal-plan/{plan_id}
```

---

## 🗂️ Data Flow

```
1. User fills form
   ↓
2. Frontend sends POST to /api/create-user
   ↓
3. API Server:
   - Calculates macros (BMR, TDEE)
   - Creates user profile in SQLite
   - Saves preferences to Chroma
   ↓
4. Calls Claude API:
   - Generates 7-day meal plan
   - Returns JSON with meals
   ↓
5. Saves meal plan:
   - Meals to SQLite
   - Context to Chroma
   ↓
6. Returns response to frontend
   ↓
7. Frontend displays meal plan
```

---

## 🧪 Testing the Flow

### Test 1: Health Check
```bash
curl http://localhost:5000/api/health
```

Expected:
```json
{
  "status": "healthy",
  "service": "NutriGenie API",
  "timestamp": "2025-10-25T06:00:00"
}
```

### Test 2: Create User (Minimal)
```bash
curl -X POST http://localhost:5000/api/create-user \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "age": 25,
    "sex": "female",
    "height": 165,
    "weight": 60,
    "activity_level": "lightly_active",
    "goal_type": "maintain",
    "diet_type": "vegetarian",
    "meals_per_day": 3,
    "cooking_time_max": 30,
    "allergies": [],
    "medical_conditions": [],
    "cuisine_preferences": []
  }'
```

Expected:
```json
{
  "status": "success",
  "message": "Meal plan created successfully with 21 meals",
  "user_id": "uuid-here",
  "plan_id": "uuid-here",
  "macros": {...},
  "meal_plan": {...}
}
```

---

## ❌ Error Handling

### Claude API Not Working
**Error:**
```json
{
  "status": "error",
  "message": "Claude API is not working. Please check your API key and try again.",
  "error_type": "claude_api_error"
}
```

**Solution:**
1. Check `.env` file has correct `ANTHROPIC_API_KEY`
2. Verify API key is valid
3. Check API quota/limits

### Server Not Running
**Error in Browser:**
```
Connection Error
Could not connect to the API server.
Make sure the server is running: python api_server.py
```

**Solution:**
```bash
# Start the server
python api_server.py
```

### Missing Required Fields
**Error:**
```json
{
  "status": "error",
  "message": "Missing required fields: age, sex, height"
}
```

**Solution:** Fill out all required fields in the form

---

## 📊 Database Inspection

### View Created Users
```bash
sqlite3 data/nutrigenie.db "SELECT * FROM users;"
```

### View Meal Plans
```bash
sqlite3 data/nutrigenie.db "SELECT * FROM meal_plans;"
```

### View Meals
```bash
sqlite3 data/nutrigenie.db "SELECT recipe_name, calories FROM planned_meals LIMIT 10;"
```

### View Chroma Data
```python
from db.chroma_db import ChromaDB

chroma = ChromaDB()
convs = chroma.collections['conversations'].get()
print(f"Conversations: {len(convs['ids'])}")
```

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use different port
python api_server.py --port 5001
```

### Database Locked
```bash
# Close all connections
pkill python

# Reset database
rm -rf data/
python test_system.py
```

### CORS Issues
Already handled with `flask-cors`. If issues persist:
```python
# In api_server.py
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

---

## 📁 File Structure

```
NutriGenie/
├── api_server.py           # ✅ NEW - Flask API server
├── first_agent.py          # Nutrition Planner Agent
├── db/                     # Database layer
│   ├── sqlite_db.py
│   ├── chroma_db.py
│   └── memory.py
├── frontend/
│   ├── user_form.html      # ✅ UPDATED - Connected to API
│   └── meal_plan.html      # ✅ NEW - Display results
├── data/                   # Auto-created databases
│   ├── nutrigenie.db
│   └── chroma_db/
└── requirements.txt        # ✅ UPDATED - Added Flask
```

---

## 🎯 What's Working Now

✅ **User Form** - Beautiful, responsive, collects all data
✅ **API Server** - Flask backend with CORS
✅ **Agent Integration** - Calls Claude for meal plans
✅ **Database Storage** - SQLite + Chroma
✅ **Meal Plan Display** - Beautiful calendar view
✅ **Error Handling** - Clear error messages
✅ **Loading States** - User feedback during generation

---

## 🚀 Next Steps (Optional)

### Priority 2: Additional Features
- [ ] Shopping list generation
- [ ] Recipe details page
- [ ] Print/PDF export
- [ ] Email meal plan

### Priority 3: Additional Agents
- [ ] Grocery Scout Agent
- [ ] Diet Coach Agent (conversational)
- [ ] Progress Tracker Agent

---

## 💡 Demo Tips

1. **Pre-fill test data** for faster demos
2. **Have backup meal plan** in case Claude is slow
3. **Show database** to prove persistence
4. **Highlight AI features** (Claude, semantic search)
5. **Explain architecture** (hybrid database, agents)

---

## ✨ You're Ready!

The complete flow is connected and working:

**Form → API → Agent → Database → Display**

Start the server and try it out! 🎉

```bash
python api_server.py
```

Then open: http://localhost:5000
