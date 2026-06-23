"""
=============================================================
GEMINI LLM SERVICE
=============================================================
Manages all interactions with the Google Gemini model using LangChain.
Key functions:
1. Parse user queries into structured filters (Query Understanding).
2. Accumulate filters across a conversation history (Conversational Search).
3. Generate natural language explanations for food recommendations.
=============================================================
"""

import json
import logging
from typing import List, Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from models.ai_models import QueryFilters
import config

logger = logging.getLogger(__name__)


class LLMService:
    """Service to wrap Gemini LLM capabilities using LangChain."""

    def __init__(self):
        self.enabled = False
        self.llm = None
        self.structured_llm = None

        if not config.GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY is not set in environment. LLM functions will fail.")
            return

        try:
            # Initialize ChatGoogleGenerativeAI with zero temperature for analytical tasks
            self.llm = ChatGoogleGenerativeAI(
                model=config.LLM_MODEL,
                google_api_key=config.GEMINI_API_KEY,
                temperature=0.0
            )
            # Bind the QueryFilters Pydantic model for structured outputs
            self.structured_llm = self.llm.with_structured_output(QueryFilters)
            self.enabled = True
            logger.info(f"✅ Gemini LLM initialized with model: {config.LLM_MODEL}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini Chat LLM: {str(e)}")

    def parse_query_intent(self, query: str) -> QueryFilters:
        """
        Parse a single user query to extract structured menu filters.
        
        Args:
            query: User's search query (e.g. "spicy chicken under 300")
            
        Returns:
            QueryFilters: Parsed filters structure
        """
        if not self.enabled or not self.structured_llm:
            logger.warning("⚠️ GEMINI_API_KEY not configured. Using rule-based fallback parser.")
            import re
            
            # Simple rule-based extraction
            q_lower = query.lower()
            
            # 1. Price
            max_price = None
            price_match = re.search(r'(?:under|below|less than|max|budget)\s*(\d+)', q_lower)
            if price_match:
                max_price = float(price_match.group(1))
                
            # 2. Veg / Nonveg
            veg_or_nonveg = None
            if "nonveg" in q_lower or "chicken" in q_lower or "pepperoni" in q_lower or "meat" in q_lower:
                veg_or_nonveg = "nonveg"
            elif "veg" in q_lower or "vegetarian" in q_lower or "vegan" in q_lower:
                veg_or_nonveg = "veg"
                
            # 3. Cuisine
            cuisine = None
            for c in ["italian", "indian", "chinese", "american", "south indian"]:
                if c in q_lower:
                    cuisine = c.title()
                    
            # 4. Spice Level
            spice_level = None
            if "spicy" in q_lower or "hot" in q_lower or "masala" in q_lower or "chili" in q_lower:
                spice_level = "spicy"
            elif "mild" in q_lower:
                spice_level = "mild"
                
            # 5. Taste Preference
            taste_preference = None
            for t in ["cheesy", "crispy", "creamy", "sweet", "sour", "savory"]:
                if t in q_lower:
                    taste_preference = t
                    
            # 6. Meal Type
            meal_type = None
            for m in ["breakfast", "lunch", "dinner", "snack", "dessert"]:
                if m in q_lower:
                    meal_type = m
                    
            # 7. Semantic Intent (Clean of prices and cuisines)
            intent = query
            # Strip out "under 300" etc.
            intent = re.sub(r'(?:under|below|less than|max|budget)\s*\d+', '', intent, flags=re.I)
            # Clean common words
            intent = re.sub(r'\b(veg|nonveg|vegetarian|spicy|crispy|cheesy|creamy|sweet|cheap|filling|healthy|options|meals?|food)\b', '', intent, flags=re.I)
            intent = re.sub(r'\s+', ' ', intent).strip()
            if not intent:
                intent = query
                
            return QueryFilters(
                cuisine=cuisine,
                max_price=max_price,
                veg_or_nonveg=veg_or_nonveg,
                spice_level=spice_level,
                taste_preference=taste_preference,
                meal_type=meal_type,
                semantic_intent=intent
            )

        system_instruction = (
            "You are an expert query parser for a food ordering platform. "
            "Your task is to analyze the user's query and extract matching filters. "
            "Follow these rules strictly:\n"
            "1. 'veg_or_nonveg': set to 'veg' if they specify vegetarian, veg, or vegan food. "
            "Set to 'nonveg' if they mention meat, chicken, pepperoni, mutton, etc. Otherwise, set to null.\n"
            "2. 'max_price': extract the maximum price/budget as a number (e.g., 'under 300' -> 300).\n"
            "3. 'cuisine': extract the cuisine (e.g., Indian, Chinese, Italian, South Indian).\n"
            "4. 'spice_level': extract spice preference (e.g., spicy, mild, medium, none).\n"
            "5. 'taste_preference': extract texture/taste (e.g. crispy, cheesy, creamy, sweet).\n"
            "6. 'meal_type': extract meal category (e.g., breakfast, lunch, dinner, snack, dessert).\n"
            "7. 'semantic_intent': extract the core dish or category searched for, stripped of filters "
            "(e.g., 'crispy vegetarian snacks' -> 'snacks', 'spicy chicken under 300' -> 'chicken').\n"
            "If a parameter is not specified or cannot be inferred, set it to null."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            ("user", "Extract filters from: '{query}'")
        ])

        try:
            chain = prompt | self.structured_llm
            result = chain.invoke({"query": query})
            logger.info(f"Parsed query intent for '{query}': {result}")
            return result
        except Exception as e:
            logger.error(f"Error parsing query intent with Gemini: {str(e)}")
            return QueryFilters(semantic_intent=query)

    def accumulate_conversation_filters(
        self, 
        current_query: str, 
        history_messages: List[Dict[str, str]]
    ) -> QueryFilters:
        """
        Analyze chat history and current query to produce the accumulated active filters.
        
        Args:
            current_query: The user's latest query
            history_messages: List of prior messages, e.g. [{"role": "user", "content": "spicy"}, ...]
            
        Returns:
            QueryFilters: Merged filter state
        """
        if not self.enabled or not self.structured_llm:
            logger.warning("⚠️ GEMINI_API_KEY not configured. Accumulating conversational filters via history concatenation.")
            combined = ""
            for msg in history_messages:
                if msg["role"] == "user":
                    combined += msg["content"] + " "
            combined += current_query
            return self.parse_query_intent(combined)

        # Build a visual history block for the prompt
        history_str = ""
        for msg in history_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_str += f"{role}: {msg['content']}\n"

        system_instruction = (
            "You are an AI assistant for a food ordering app tracking conversation history.\n"
            "Your task is to output the cumulative set of active QueryFilters based on the dialogue history "
            "and the user's latest message.\n\n"
            "Rules:\n"
            "1. Accumulate constraints: If they said 'I want pizza' and then 'under 300', the semantic_intent is 'pizza' "
            "and max_price is 300.\n"
            "2. Update constraints if they change their mind: If they first said 'spicy' but now say 'actually, mild', "
            "set spice_level to 'mild'.\n"
            "3. Clean fields if they cancel: If they say 'forget the budget', set max_price to null.\n"
            "4. Return the updated QueryFilters state."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            ("user", "Conversation History:\n{history}\n\nLatest User Query: '{query}'\n\nGenerate updated QueryFilters.")
        ])

        try:
            chain = prompt | self.structured_llm
            result = chain.invoke({"history": history_str, "query": current_query})
            logger.info(f"Accumulated conversational filters: {result}")
            return result
        except Exception as e:
            logger.error(f"Error accumulating conversation filters: {str(e)}")
            return QueryFilters(semantic_intent=current_query)

    def generate_recommendation_reason(
        self, 
        query_or_intent: str, 
        item_name: str, 
        restaurant_name: str, 
        description: str,
        rating: float,
        price: float,
        reviews_summary: str
    ) -> str:
        """
        Generate a natural language explanation for why an item was recommended.
        
        Args:
            query_or_intent: User query / semantic intent
            item_name: Name of the food item
            restaurant_name: Name of the restaurant
            description: Description of the food item
            rating: Rating of the item
            price: Price of the item
            reviews_summary: Reviews metadata or concatenated text
            
        Returns:
            str: 1-2 sentence reason
        """
        if not self.enabled or not self.llm:
            return f"This delicious '{item_name}' from '{restaurant_name}' fits your preference for {query_or_intent}. It is rated {rating} stars and costs Rs. {price}."

        system_instruction = (
            "You are a friendly food concierge recommending dishes to customers. "
            "Write a concise explanation (exactly 1 or 2 short sentences) explaining why this specific dish "
            "fits the user's search query or preference. "
            "Be enthusiastic but brief. Focus on sensory words (e.g. crispy, savory, creamy) matching the food, "
            "its high rating, and positive review highlights if available."
        )

        user_content = (
            f"User Preference: '{query_or_intent}'\n"
            f"Dish: {item_name} from {restaurant_name}\n"
            f"Description: {description}\n"
            f"Price: Rs. {price}\n"
            f"Rating: {rating}/5\n"
            f"Reviews mention: '{reviews_summary}'\n\n"
            "Recommendation Reason:"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            ("user", user_content)
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({})
            reason_text = response.content.strip() if hasattr(response, 'content') else str(response)
            return reason_text
        except Exception as e:
            logger.error(f"Error generating recommendation reason: {str(e)}")
            return f"Delicious {item_name} from {restaurant_name}, rated {rating} stars."

    def generate_conversational_response(
        self, 
        current_query: str, 
        history_messages: List[Dict[str, str]], 
        items: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a conversational natural language reply summarizing the search results.
        
        Args:
            current_query: The user's latest query
            history_messages: Dialog history
            items: Retrieve food item dicts
            
        Returns:
            str: 2-3 sentence conversational response
        """
        if not self.enabled or not self.llm:
            return "Here are the best matches I found for your request."

        history_str = ""
        for msg in history_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_str += f"{role}: {msg['content']}\n"

        items_summary = ""
        for idx, item in enumerate(items[:5]):
            cuisine = item.get("cuisine", [])
            if isinstance(cuisine, List):
                cuisine = ",".join(cuisine)
            if not cuisine:
                cuisine = "Not available"

            items_summary += (
                f"{idx+1}. {item['item_name']} "
                f"from {item['restaurant_name']} "
                f"(Price: Rs. {item['price']}, "
                f"Rating: {item['rating']}/5, "
                f"Cuisine: {cuisine})\n"
            )
        system_instruction = (
            "You are a warm, friendly AI food concierge. "
            "Your task is to write a brief conversational response (exactly 2 or 3 sentences) "
            "summarizing the search results found for the user's latest query. "
            "Highlight the top 1 or 2 options. Directly refer to the user's constraints if they specified them "
            "(e.g. if they wanted spicy, vegetarian, or cheap meals). Keep it engaging and natural. "
            "Do NOT reference internal scores or ranking parameters."
        )

        user_content = (
            f"Conversation History:\n{history_str}\n"
            f"Latest Query: '{current_query}'\n\n"
            f"Search Results:\n{items_summary}\n\n"
            "Conversational Response:"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            ("user", user_content)
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({})
            response_text = response.content.strip() if hasattr(response, 'content') else str(response)
            return response_text
        except Exception as e:
            logger.error(f"Error generating conversational response: {str(e)}")
            if items:
                return f"I found some options for you! I highly recommend the {items[0]['item_name']} from {items[0]['restaurant_name']}."
            return "I couldn't find any items matching your preferences. Can I help you find something else?"

