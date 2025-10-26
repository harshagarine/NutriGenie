"""
Product Finder Agent - Second Agent
Queries MCP server to find product suggestions for meal plan ingredients.
"""

from uagents import Agent, Context, Model
from db.memory import get_memory
from typing import Dict, List, Any, Optional
import anthropic
import os
from dotenv import load_dotenv
import json
import requests

load_dotenv()

# Initialize memory
memory = get_memory()

# Initialize Claude API with MCP support
claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# MCP Server Configuration
MCP_SERVER_URL = "https://openfoodfacts-mcp.onrender.com/mcp"
# MCP_SERVER_URL = "https://nona-euryphagous-laraine.ngrok-free.dev/mcp"

# Global MCP session storage
mcp_session_id = None
mcp_session_lock = None
# Use requests.Session() for persistent connection
mcp_session = None


# Define message models
class IngredientListRequest(Model):
    """Request to find products for ingredients from a meal plan."""
    plan_id: str
    user_id: str


class ProductSuggestion(Model):
    """Model for a single product suggestion."""
    ingredient: str
    products: List[Dict[str, Any]]


class ProductSuggestionsResponse(Model):
    """Response containing product suggestions for all ingredients."""
    plan_id: str
    user_id: str
    status: str
    message: str
    suggestions: Optional[List[Dict[str, Any]]] = None


# Create the Product Finder Agent
product_finder_agent = Agent(
    name="product_finder",
    seed="product_finder_seed_phrase_nutrigenie",
    port=8002,
    endpoint=["http://localhost:8002/submit"]
)


async def initialize_mcp_session(ctx: Context) -> Optional[str]:
    """
    Initialize MCP session with the server.
    Uses requests.Session() for persistent connections.
    Returns session ID if successful, None otherwise.
    """
    global mcp_session_id, mcp_session

    if mcp_session_id and mcp_session:
        ctx.logger.info(f"♻️  Reusing existing MCP session: {mcp_session_id}")
        return mcp_session_id

    try:
        ctx.logger.info("🔌 Initializing MCP session with persistent connection...")

        # Create persistent session
        if not mcp_session:
            mcp_session = requests.Session()
            ctx.logger.info("Created new requests.Session() for persistent connection")

        # Initialize request according to MCP protocol
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "prompts": {},
                    "resources": {}
                },
                "clientInfo": {
                    "name": "NutriGenie-ProductFinder",
                    "version": "1.0.0"
                }
            }
        }

        response = mcp_session.post(
            MCP_SERVER_URL,
            json=init_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"  # Server requires BOTH!
            },
            timeout=30
        )

        ctx.logger.info(f"MCP Response Status: {response.status_code}")
        ctx.logger.info(f"MCP Response Headers: {dict(response.headers)}")
        ctx.logger.info(f"MCP Response Body (full): {response.text}")
        ctx.logger.info(f"MCP Response Cookies: {dict(response.cookies)}")
        ctx.logger.info(f"Session Cookies after init: {dict(mcp_session.cookies)}")

        if response.status_code == 200:
            data = response.json()
            ctx.logger.info(f"Parsed JSON response: {json.dumps(data, indent=2)[:1000]}")

            # Get session ID from response headers (your server uses Mcp-Session-Id)
            session_id = (
                response.headers.get('Mcp-Session-Id') or
                response.headers.get('mcp-session-id') or
                response.headers.get('x-session-id') or
                response.headers.get('X-Session-Id') or
                response.headers.get('session-id') or
                response.headers.get('Session-Id') or
                mcp_session.cookies.get('session_id') or
                mcp_session.cookies.get('sessionId') or
                data.get('result', {}).get('meta', {}).get('sessionId') or  # Check meta
                data.get('result', {}).get('sessionId') or
                data.get('meta', {}).get('sessionId') or  # Check root meta
                data.get('sessionId')
            )

            ctx.logger.info(f"Session ID extracted: {session_id}")

            if session_id:
                mcp_session_id = session_id
                ctx.logger.info(f"✅ MCP session initialized: {session_id}")
                return session_id
            else:
                # MCP server may be using cookie-based sessions
                # The requests.Session() will automatically handle cookies
                ctx.logger.warning("⚠️  No explicit session ID found")
                ctx.logger.info("✅ Using persistent HTTP session (cookie-based)")
                ctx.logger.info(f"Session has {len(mcp_session.cookies)} cookies")

                # Mark as initialized with persistent connection
                mcp_session_id = "persistent"
                return mcp_session_id
        else:
            ctx.logger.error(f"❌ MCP initialization failed: {response.status_code}")
            ctx.logger.error(f"Response: {response.text}")
            return None

    except Exception as e:
        ctx.logger.error(f"❌ Error initializing MCP session: {str(e)}")
        import traceback
        ctx.logger.error(traceback.format_exc())
        return None


async def list_mcp_tools(ctx: Context) -> List[Dict[str, Any]]:
    """
    List available tools from MCP server.
    Returns list of tool definitions.
    """
    global mcp_session_id, mcp_session

    if not mcp_session_id or not mcp_session:
        ctx.logger.error("Cannot list tools: No MCP session")
        return []

    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if mcp_session_id not in ["stateless", "persistent"]:
            headers["Mcp-Session-Id"] = mcp_session_id

        list_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        }

        response = mcp_session.post(
            MCP_SERVER_URL,
            json=list_request,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if 'result' in data and 'tools' in data['result']:
                tools = data['result']['tools']
                ctx.logger.info(f"📋 Available tools: {[t['name'] for t in tools]}")
                return tools
            else:
                ctx.logger.warning(f"No tools found in response: {data}")
                return []
        else:
            ctx.logger.error(f"Failed to list tools: {response.status_code}")
            return []

    except Exception as e:
        ctx.logger.error(f"Error listing tools: {str(e)}")
        return []


@product_finder_agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event."""
    ctx.logger.info(f"🛒 Product Finder Agent started!")
    ctx.logger.info(f"Agent address: {product_finder_agent.address}")
    ctx.logger.info(f"MCP Server: {MCP_SERVER_URL}")

    # Initialize MCP session on startup
    session_id = await initialize_mcp_session(ctx)

    if session_id:
        # List available tools to see what's available
        await list_mcp_tools(ctx)


def extract_unique_ingredients(meal_plan: Dict[str, Any]) -> List[str]:
    """
    Extract unique ingredients from a meal plan.
    Returns a deduplicated list of ingredient names.
    """
    ingredients_set = set()

    meals = meal_plan.get('meals', [])
    for meal in meals:
        ingredients = meal.get('ingredients', [])
        for ingredient in ingredients:
            # Normalize ingredient name (lowercase, strip whitespace)
            normalized = ingredient.lower().strip()
            ingredients_set.add(normalized)

    return sorted(list(ingredients_set))


async def query_mcp_for_products(
    ctx: Context,
    ingredient: str,
    top_n: int = 3
) -> List[Dict[str, Any]]:
    """
    Query MCP server for products matching an ingredient.
    Uses MCP protocol to search OpenFoodFacts database.

    Args:
        ctx: Agent context for logging
        ingredient: Ingredient name to search for
        top_n: Number of top products to return

    Returns:
        List of product dictionaries with details
    """
    global mcp_session_id, mcp_session

    try:
        # Ensure we have a session
        if not mcp_session_id or not mcp_session:
            ctx.logger.info("No MCP session, initializing...")
            mcp_session_id = await initialize_mcp_session(ctx)

        if not mcp_session_id or not mcp_session:
            ctx.logger.error("❌ Cannot query MCP: No session")
            return []

        # Call the search tool using JSON-RPC format
        ctx.logger.info(f"🔍 Searching for products matching '{ingredient}'...")

        # Build headers with session ID (your server expects Mcp-Session-Id)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"  # Server requires BOTH!
        }
        if mcp_session_id and mcp_session_id not in ["stateless", "persistent"]:
            # Your MCP server expects "Mcp-Session-Id" header (case-sensitive)
            headers["Mcp-Session-Id"] = mcp_session_id
            ctx.logger.info(f"Sending request with session ID: {mcp_session_id}")

        # Call the search tool with JSON-RPC
        # Tool name is "searchProducts" (camelCase), not "search_products"
        search_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "searchProducts",  # Correct tool name!
                "arguments": {
                    "query": ingredient,
                    "page": 1,
                    "pageSize": top_n * 3  # Changed to camelCase
                }
            }
        }

        ctx.logger.debug(f"Sending request: {json.dumps(search_request, indent=2)}")
        ctx.logger.info(f"Using persistent session with {len(mcp_session.cookies)} cookies")

        # Use the persistent session for the request
        response = mcp_session.post(
            MCP_SERVER_URL,
            json=search_request,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            ctx.logger.error(f"MCP server error for '{ingredient}': {response.status_code}")
            ctx.logger.error(f"Response: {response.text}")
            return []

        data = response.json()
        ctx.logger.info(f"MCP Response Status: {response.status_code}")
        ctx.logger.debug(f"MCP Response: {json.dumps(data, indent=2)[:1000]}")

        products = []

        # Extract products from JSON-RPC response
        # JSON-RPC format: {"jsonrpc": "2.0", "id": 2, "result": {...}}
        if 'result' in data:
            result = data['result']

            # Check if result contains content array (MCP protocol)
            if isinstance(result, dict) and 'content' in result:
                content_items = result.get('content', [])
                for item in content_items:
                    if item.get('type') == 'text':
                        text_content = item.get('text', '')
                        try:
                            # Try to parse as JSON
                            parsed_content = json.loads(text_content)
                            if isinstance(parsed_content, dict):
                                products = parsed_content.get('products', parsed_content.get('results', []))
                            elif isinstance(parsed_content, list):
                                products = parsed_content
                            break
                        except json.JSONDecodeError:
                            ctx.logger.warning(f"Could not parse text as JSON: {text_content[:200]}...")

            # Check if result is directly a list or dict with products
            elif isinstance(result, list):
                products = result
            elif isinstance(result, dict):
                products = result.get('products', result.get('results', []))

        # Fallback: check for 'error' in JSON-RPC response
        elif 'error' in data:
            error = data['error']
            ctx.logger.error(f"MCP returned error: {error.get('message', error)}")
            return []

        if not products:
            ctx.logger.warning(f"⚠️  No products found for '{ingredient}'")
            return []

        ctx.logger.info(f"📦 Got {len(products)} products from MCP server")

        # Debug: Log first product structure to see field names
        if products:
            ctx.logger.info(f"Sample product structure: {json.dumps(products[0], indent=2)}")

        # Sort by nutri-score (A > B > C > D > E)
        nutri_score_rank = {'a': 5, 'b': 4, 'c': 3, 'd': 2, 'e': 1}

        def get_nutri_score_value(product):
            # OpenFoodFacts MCP returns 'nutriScore' (camelCase)
            score = product.get('nutriScore', product.get('nutri_score', product.get('nutrition_grade', 'unknown')))
            if isinstance(score, str):
                score = score.lower()
                if score == 'unknown':
                    return 0  # Put unknowns at the end
            else:
                score = 'unknown'
            return nutri_score_rank.get(score, 0)

        products_sorted = sorted(
            products,
            key=get_nutri_score_value,
            reverse=True
        )

        # Return top N products
        top_products = products_sorted[:top_n]

        # Format the response - get full details for each product
        formatted_products = []
        for product in top_products:
            barcode = product.get('barcode', product.get('id'))

            # Try to get full product details if barcode available
            full_product = None
            if barcode:
                try:
                    ctx.logger.debug(f"Fetching full details for barcode: {barcode}")
                    detail_request = {
                        "jsonrpc": "2.0",
                        "id": f"detail_{barcode}",
                        "method": "tools/call",
                        "params": {
                            "name": "getProductByBarcode",
                            "arguments": {"barcode": str(barcode)}
                        }
                    }
                    detail_response = mcp_session.post(
                        MCP_SERVER_URL,
                        json=detail_request,
                        headers=headers,
                        timeout=10
                    )
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        ctx.logger.info(f"Detail response for {barcode}: {json.dumps(detail_data, indent=2)[:800]}")
                        if 'result' in detail_data and 'content' in detail_data['result']:
                            for item in detail_data['result']['content']:
                                if item.get('type') == 'text':
                                    try:
                                        full_product = json.loads(item['text'])
                                        ctx.logger.info(f"Parsed full product keys: {list(full_product.keys())}")
                                        break
                                    except Exception as parse_err:
                                        ctx.logger.warning(f"Could not parse text: {parse_err}")
                                        pass
                except Exception as e:
                    ctx.logger.warning(f"Could not fetch details for {barcode}: {e}")

            # Use full product data if available, otherwise use search result
            data_source = full_product if full_product else product

            # Your MCP server returns 'nutritionFacts' (not 'nutriments')
            nutrition = data_source.get('nutritionFacts', data_source.get('nutriments', {}))

            ctx.logger.debug(f"Nutrition data for {barcode}: {nutrition}")

            formatted_products.append({
                'product_name': product.get('name', product.get('product_name', 'Unknown')),
                'brand': product.get('brand', product.get('brands', 'Unknown')),
                'nutri_score': product.get('nutriScore', product.get('nutri_score', product.get('nutrition_grade', 'unknown'))).upper() if product.get('nutriScore') not in [None, 'unknown'] else 'N/A',
                'calories_per_100g': nutrition.get('energy', nutrition.get('energy-kcal_100g', nutrition.get('energy_100g', 0))),
                'protein_per_100g': nutrition.get('proteins', nutrition.get('proteins_100g', 0)),
                'carbs_per_100g': nutrition.get('carbohydrates', nutrition.get('carbohydrates_100g', 0)),
                'fats_per_100g': nutrition.get('fat', nutrition.get('fat_100g', 0)),
                'product_url': f"https://world.openfoodfacts.org/product/{barcode}" if barcode else '',
                'image_url': product.get('imageUrl', product.get('image_url', product.get('image', '')))
            })

        ctx.logger.info(f"✅ Found {len(formatted_products)} products for '{ingredient}'")
        return formatted_products

    except requests.exceptions.Timeout:
        ctx.logger.error(f"⏱️ Timeout querying MCP server for '{ingredient}'")
        return []
    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"❌ Network error for '{ingredient}': {str(e)}")
        return []
    except Exception as e:
        ctx.logger.error(f"❌ Error querying MCP for '{ingredient}': {str(e)}")
        return []


@product_finder_agent.on_message(model=IngredientListRequest)
async def handle_ingredient_list(ctx: Context, sender: str, msg: IngredientListRequest):
    """
    Handle ingredient list and find product suggestions.
    This is the main workflow for the Product Finder Agent.
    """
    ctx.logger.info(f"📥 Received ingredient list request from {sender}")
    ctx.logger.info(f"Plan ID: {msg.plan_id}, User ID: {msg.user_id}")

    try:
        # Step 1: Get meal plan from memory
        ctx.logger.info("🔍 Loading meal plan from memory...")
        meal_plan = memory.get_meal_plan(msg.plan_id)

        if not meal_plan:
            ctx.logger.error(f"❌ Meal plan not found: {msg.plan_id}")
            response = ProductSuggestionsResponse(
                plan_id=msg.plan_id,
                user_id=msg.user_id,
                status="error",
                message=f"Meal plan not found: {msg.plan_id}"
            )
            await ctx.send(sender, response)
            return

        # Step 2: Extract unique ingredients
        ctx.logger.info("🥕 Extracting unique ingredients...")
        unique_ingredients = extract_unique_ingredients(meal_plan)
        ctx.logger.info(f"Found {len(unique_ingredients)} unique ingredients")

        if not unique_ingredients:
            ctx.logger.warning("⚠️ No ingredients found in meal plan")
            response = ProductSuggestionsResponse(
                plan_id=msg.plan_id,
                user_id=msg.user_id,
                status="success",
                message="No ingredients found in meal plan",
                suggestions=[]
            )
            await ctx.send(sender, response)
            return

        # Step 3: Query MCP server for each ingredient
        ctx.logger.info("🛒 Querying MCP server for product suggestions...")
        all_suggestions = []

        for ingredient in unique_ingredients:
            ctx.logger.info(f"Searching products for: {ingredient}")
            products = await query_mcp_for_products(ctx, ingredient, top_n=3)

            suggestion = {
                'ingredient': ingredient,
                'products': products,
                'product_count': len(products)
            }
            all_suggestions.append(suggestion)

        # Step 4: Calculate statistics
        total_products = sum(s['product_count'] for s in all_suggestions)
        ingredients_with_products = sum(1 for s in all_suggestions if s['product_count'] > 0)

        ctx.logger.info(f"✅ Found {total_products} total products for {ingredients_with_products}/{len(unique_ingredients)} ingredients")

        # Step 5: Send response
        response = ProductSuggestionsResponse(
            plan_id=msg.plan_id,
            user_id=msg.user_id,
            status="success",
            message=f"Found {total_products} product suggestions for {len(unique_ingredients)} ingredients",
            suggestions=all_suggestions
        )

        await ctx.send(sender, response)

    except Exception as e:
        ctx.logger.error(f"❌ Error processing ingredient list: {e}")
        response = ProductSuggestionsResponse(
            plan_id=msg.plan_id,
            user_id=msg.user_id,
            status="error",
            message=f"Error: {str(e)}"
        )
        await ctx.send(sender, response)


@product_finder_agent.on_interval(period=60.0)
async def log_status(ctx: Context):
    """Periodic status log."""
    ctx.logger.info("🛒 Product Finder Agent is running...")


if __name__ == "__main__":
    print("🚀 Starting Product Finder Agent...")
    print(f"Agent Address: {product_finder_agent.address}")
    print(f"MCP Server: {MCP_SERVER_URL}")
    product_finder_agent.run()
