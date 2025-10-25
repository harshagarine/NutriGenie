"""
Chroma Vector Database for semantic memory storage.
Handles conversations, food feedback, and semantic preferences.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
import os


class ChromaDB:
    def __init__(self, db_path: str = "./data/chroma_db"):
        """Initialize Chroma vector database."""
        # Ensure data directory exists
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collections = {}
        self._create_collections()
    
    def _create_collections(self):
        """Create all necessary collections."""
        
        # Collection 1: Conversations
        self.collections['conversations'] = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Chat history with agents"}
        )
        
        # Collection 2: Food Feedback
        self.collections['food_feedback'] = self.client.get_or_create_collection(
            name="food_feedback",
            metadata={"description": "User ratings and feedback on meals"}
        )
        
        # Collection 3: Preference Embeddings
        self.collections['preferences'] = self.client.get_or_create_collection(
            name="preferences",
            metadata={"description": "Semantic food preferences and dislikes"}
        )
        
        print("✅ Chroma collections created successfully")
    
    # ============ CONVERSATION OPERATIONS ============
    
    def add_conversation(
        self, 
        user_id: str, 
        agent: str, 
        role: str, 
        message: str,
        session_id: Optional[str] = None
    ) -> str:
        """Add a conversation message."""
        conv_id = f"conv_{user_id}_{uuid.uuid4().hex[:8]}"
        
        self.collections['conversations'].add(
            ids=[conv_id],
            documents=[message],
            metadatas=[{
                "user_id": user_id,
                "agent": agent,
                "role": role,  # 'user' or 'agent'
                "session_id": session_id or "default",
                "timestamp": datetime.now().isoformat()
            }]
        )
        
        return conv_id
    
    def search_conversations(
        self, 
        user_id: str, 
        query: str, 
        n_results: int = 5,
        agent: Optional[str] = None
    ) -> List[Dict]:
        """Search conversation history semantically."""
        where_filter = {"user_id": user_id}
        if agent:
            where_filter["agent"] = agent
        
        results = self.collections['conversations'].query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        return self._format_results(results)
    
    def get_recent_conversations(
        self, 
        user_id: str, 
        n_results: int = 10,
        agent: Optional[str] = None
    ) -> List[Dict]:
        """Get recent conversations for a user."""
        where_filter = {"user_id": user_id}
        if agent:
            where_filter["agent"] = agent
        
        results = self.collections['conversations'].get(
            where=where_filter,
            limit=n_results
        )
        
        return self._format_get_results(results)
    
    # ============ FOOD FEEDBACK OPERATIONS ============
    
    def add_food_feedback(
        self,
        user_id: str,
        meal_id: Optional[str],
        food_description: str,
        rating: int,
        feedback_text: str,
        cuisine: Optional[str] = None
    ) -> str:
        """Add user feedback on a meal."""
        feedback_id = f"feedback_{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Combine description and feedback for better semantic search
        document = f"{food_description}. {feedback_text}"
        
        metadata = {
            "user_id": user_id,
            "rating": rating,
            "timestamp": datetime.now().isoformat()
        }
        
        if meal_id:
            metadata["meal_id"] = meal_id
        if cuisine:
            metadata["cuisine"] = cuisine
        
        self.collections['food_feedback'].add(
            ids=[feedback_id],
            documents=[document],
            metadatas=[metadata]
        )
        
        return feedback_id
    
    def search_liked_foods(
        self,
        user_id: str,
        query: str,
        min_rating: int = 4,
        n_results: int = 10
    ) -> List[Dict]:
        """Search for foods user liked."""
        results = self.collections['food_feedback'].query(
            query_texts=[query],
            n_results=n_results,
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"rating": {"$gte": min_rating}}
                ]
            }
        )
        
        return self._format_results(results)
    
    def search_disliked_foods(
        self,
        user_id: str,
        query: str,
        max_rating: int = 2,
        n_results: int = 10
    ) -> List[Dict]:
        """Search for foods user disliked."""
        results = self.collections['food_feedback'].query(
            query_texts=[query],
            n_results=n_results,
            where={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"rating": {"$lte": max_rating}}
                ]
            }
        )
        
        return self._format_results(results)
    
    def get_all_feedback(self, user_id: str) -> List[Dict]:
        """Get all feedback for a user."""
        results = self.collections['food_feedback'].get(
            where={"user_id": user_id}
        )
        
        return self._format_get_results(results)
    
    # ============ PREFERENCE OPERATIONS ============
    
    def add_preference(
        self,
        user_id: str,
        preference_text: str,
        preference_type: str,  # 'like', 'dislike', 'texture', 'flavor', etc.
        strength: str = "moderate"  # 'strong', 'moderate', 'mild'
    ) -> str:
        """Add a semantic preference."""
        pref_id = f"pref_{user_id}_{uuid.uuid4().hex[:8]}"
        
        self.collections['preferences'].add(
            ids=[pref_id],
            documents=[preference_text],
            metadatas=[{
                "user_id": user_id,
                "preference_type": preference_type,
                "strength": strength,
                "timestamp": datetime.now().isoformat()
            }]
        )
        
        return pref_id
    
    def search_preferences(
        self,
        user_id: str,
        query: str,
        preference_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """Search user preferences semantically."""
        where_filter = {"user_id": user_id}
        if preference_type:
            where_filter["preference_type"] = preference_type
        
        results = self.collections['preferences'].query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        return self._format_results(results)
    
    def get_all_preferences(self, user_id: str) -> List[Dict]:
        """Get all preferences for a user."""
        results = self.collections['preferences'].get(
            where={"user_id": user_id}
        )
        
        return self._format_get_results(results)
    
    # ============ HELPER METHODS ============
    
    def _format_results(self, results: Dict) -> List[Dict]:
        """Format query results into a list of dictionaries."""
        formatted = []
        
        if not results['ids'] or not results['ids'][0]:
            return formatted
        
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted
    
    def _format_get_results(self, results: Dict) -> List[Dict]:
        """Format get results into a list of dictionaries."""
        formatted = []
        
        if not results['ids']:
            return formatted
        
        for i in range(len(results['ids'])):
            formatted.append({
                'id': results['ids'][i],
                'document': results['documents'][i],
                'metadata': results['metadatas'][i]
            })
        
        return formatted
    
    def delete_user_data(self, user_id: str):
        """Delete all data for a user (GDPR compliance)."""
        for collection in self.collections.values():
            collection.delete(where={"user_id": user_id})
    
    def reset_database(self):
        """Reset entire database (use with caution!)."""
        self.client.reset()
        self._create_collections()
