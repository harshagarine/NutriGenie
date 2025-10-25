# NutriGenie - Setup Guide

## 🌿 Your AI Nutrition & Grocery Assistant

---

## 📁 Project Structure

```
NutriGenie/
├── db/                          # Database layer
│   ├── __init__.py
│   ├── sqlite_db.py            # SQLite for structured data
│   ├── chroma_db.py            # Chroma for semantic memory
│   └── memory.py               # Unified memory interface
├── agents/                      # AI Agents (Fetch.ai)
│   └── (future agents here)
├── frontend/                    # User interface
│   └── user_form.html          # User input form
├── data/                        # Database storage (auto-created)
│   ├── nutrigenie.db           # SQLite database
│   └── chroma_db/              # Chroma vector database
├── first_agent.py              # Nutrition Planner Agent
├── test_system.py              # Test script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this!)
└── .env.example                # Example environment file
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Activate virtual environment (already created)
source venv/bin/activate

# All dependencies are already installed!
```

### 2. Configure API Keys

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
ANTHROPIC_API_KEY=your_claude_api_key_here
SQLITE_DB_PATH=./data/nutrigenie.db
CHROMA_DB_PATH=./data/chroma_db
```

### 3. Test the System

```bash
python test_system.py
```

This will:
- ✅ Create databases (SQLite + Chroma)
- ✅ Create a test user profile
- ✅ Generate a sample meal plan
- ✅ Test conversation memory
- ✅ Test food feedback
- ✅ Verify all integrations work

### 4. Run the Nutrition Planner Agent

```bash
python first_agent.py
```

The agent will start and listen for user profile requests.

### 5. Open the User Form

```bash
# Open in browser
open frontend/user_form.html
```

Fill out the form to create a user profile.

---

## 🗄️ Database Architecture

### **Hybrid Approach: SQLite + Chroma**

#### **SQLite (Structured Data)**
- ✅ User profiles (demographics, metrics)
- ✅ Goals & targets
- ✅ Restrictions (allergies, medical)
- ✅ Preferences (diet type, cuisines)
- ✅ Meal plans & meals
- ✅ Actual consumption tracking
- ✅ Modifications log

#### **Chroma (Semantic Memory)**
- ✅ Conversation history
- ✅ Food feedback (with descriptions)
- ✅ Semantic preferences

---

## 🤖 Agent Workflow

### Nutrition Planner Agent

```
1. Receive user profile data
   ↓
2. Calculate macros (BMR, TDEE, goal-based)
   ↓
3. Create user profile in memory (SQLite + Chroma)
   ↓
4. Load user context from memory
   ↓
5. Generate meal plan with Claude AI
   ↓
6. Save meal plan to memory
   ↓
7. Return meal plan to user
```

### Key Features:
- 🧮 **Smart Macro Calculation**: Uses Mifflin-St Jeor equation
- 🛡️ **Safety First**: Strictly filters allergens and medical restrictions
- 🌍 **Cultural Awareness**: Considers ethnicity and cuisine preferences
- 💾 **Persistent Memory**: Agents remember user context across sessions
- 🤖 **AI-Powered**: Uses Claude for intelligent meal planning

---

## 📊 Memory Layer API

### Creating User Profile

```python
from db.memory import get_memory

memory = get_memory()

user_id = memory.create_user_profile({
    'name': 'John Doe',
    'age': 30,
    'sex': 'male',
    'height': 175.0,
    'weight': 80.0,
    'goal_type': 'lose_weight',
    'allergies': ['peanuts'],
    'diet_type': 'omnivore',
    # ... more fields
})
```

### Getting User Context

```python
context = memory.get_user_context(user_id)
# Returns: user, goals, restrictions, preferences, conversations, feedback
```

### Creating Meal Plan

```python
plan_id = memory.create_meal_plan(
    user_id=user_id,
    week_start_date='2025-10-28',
    meals=[...],
    created_by_agent='nutrition_planner'
)
```

### Saving Conversations

```python
memory.save_conversation(
    user_id=user_id,
    agent='nutrition_planner',
    role='user',
    message='I love spicy food'
)
```

### Searching Context

```python
results = memory.search_conversation_context(
    user_id=user_id,
    query='food preferences'
)
```

---

## 🧪 Testing

### Run Full System Test

```bash
python test_system.py
```

### Manual Testing

```python
from db.memory import get_memory

memory = get_memory()

# Create user
user_id = memory.create_user_profile({...})

# Get context
context = memory.get_user_context(user_id)

# Create meal plan
plan_id = memory.create_meal_plan(...)

# Get meal plan
plan = memory.get_meal_plan(plan_id)
```

---

## 🔧 Troubleshooting

### Database Issues

```bash
# Reset databases (WARNING: deletes all data)
rm -rf data/
python test_system.py  # Recreates databases
```

### Agent Not Starting

```bash
# Check if port 8001 is available
lsof -i :8001

# Kill process if needed
kill -9 <PID>
```

### Claude API Errors

- Verify `ANTHROPIC_API_KEY` in `.env`
- Check API quota/limits
- Agent has fallback meal plan if Claude fails

---

## 📝 Next Steps

### For Hackathon:

1. **Create Second Agent**: Grocery Scout Agent
   - Searches for ingredients
   - Finds best prices
   - Generates shopping list

2. **Create Third Agent**: Diet Coach Agent
   - Conversational interface
   - Modifies meal plans based on user feedback
   - Tracks adherence

3. **Build Frontend**:
   - Display meal plans
   - Chat interface for agents
   - Progress tracking dashboard

4. **Integration**:
   - Connect form → agent → display
   - Real-time updates
   - Agent-to-agent communication

---

## 🎯 Key Features Implemented

- ✅ Hybrid database (SQLite + Chroma)
- ✅ Unified memory layer
- ✅ User profile management
- ✅ Macro calculation (BMR, TDEE)
- ✅ Fetch.ai agent integration
- ✅ Claude AI meal planning
- ✅ Conversation memory
- ✅ Food feedback tracking
- ✅ Safety restrictions
- ✅ Semantic search

---

## 📚 Documentation

- **SQLite Schema**: See `db/sqlite_db.py`
- **Chroma Collections**: See `db/chroma_db.py`
- **Memory API**: See `db/memory.py`
- **Agent Logic**: See `first_agent.py`

---

## 🤝 Team Workflow

### Person 1: Database & Backend
- ✅ Already done!
- Monitor database performance
- Add helper functions as needed

### Person 2: Nutrition Planner Agent
- ✅ Already done!
- Fine-tune Claude prompts
- Enhance meal variety and quality

### Person 3: Additional Agents
- Build Grocery Scout Agent
- Build Diet Coach Agent
- Implement agent-to-agent communication

### Person 4: Frontend
- Connect form to agent
- Build meal plan display
- Create chat interface

---

## 🚀 Ready to Build!

Everything is set up and tested. Start building your hackathon project! 🎉
