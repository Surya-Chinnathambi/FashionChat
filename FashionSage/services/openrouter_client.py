import json
import re
import aiohttp
import logging
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = "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"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",  # Required by OpenRouter
            "X-Title": "Fashion E-commerce Chatbot"
        }

    # ---------- Intent classification ----------
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify user message intent using LLM"""
        prompt = f"""
        You are an AI assistant for a fashion e-commerce platform. Analyze the user's message and classify the intent.
        
        Available intents:
        1. "product_search" - User is looking for products (clothes, shoes, accessories)
        2. "order_inquiry" - User asking about their orders, order status, tracking
        3. "general" - General questions, greetings, or other topics
        
        User message: "{message}"
        
        Respond with JSON in this exact format:
        {{
            "intent": "product_search|order_inquiry|general",
            "confidence": 0.0-1.0,
            "extracted_info": {{
                "keywords": ["keyword1", "keyword2"],
                "category": "category_if_applicable",
                "color": "color_if_mentioned",
                "price_range": "price_if_mentioned",
                "order_number": "order_number_if_mentioned"
            }}
        }}
        """

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "openrouter/auto",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 300
                }

                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    text = await response.text()
                    if response.status == 200:
                        try:
                            data = json.loads(text)
                            # support both "message" and alternate shapes
                            content = (
                                data["choices"][0].get("message", {}).get("content")
                                or data["choices"][0].get("messages", [{}])[0].get("content")
                                or ""
                            )
                            # Try to extract JSON portion robustly
                            parsed = self._extract_json_from_text(content)
                            if parsed is not None:
                                return parsed
                            # If extraction returned None, fallback to rule-based classifier
                            logger.debug("No JSON extracted from LLM content, falling back to rule-based classifier.")
                            return self._fallback_intent_classification(message)
                        except Exception as parse_err:
                            logger.error(f"Error parsing LLM JSON: {parse_err} | Raw: {text}")
                            return self._fallback_intent_classification(message)
                    else:
                        logger.error(f"OpenRouter API error: {response.status} | Raw: {text}")
                        return self._fallback_intent_classification(message)

        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return self._fallback_intent_classification(message)

    # ---------- Response generation ----------
    async def generate_response(self, intent: str, user_message: str, context_data: Optional[Dict] = None) -> str:
        """Generate appropriate response based on intent and context"""
        if intent == "product_search":
            return await self._generate_product_response(user_message, context_data)
        elif intent == "order_inquiry":
            return await self._generate_order_response(user_message, context_data)
        else:
            return await self._generate_general_response(user_message)

    async def _generate_product_response(self, message: str, context_data: Optional[Dict] = None) -> str:
        """Generate response for product search"""
        products = context_data.get("products", []) if context_data else []

        if not products:
            prompt = f"""
            The user searched for products but no matches were found.
            User message: "{message}"
            
            Generate a helpful response suggesting:
            1. Alternative search terms
            2. Popular categories we have
            3. Encouraging them to browse our collection
            
            Keep it friendly and helpful, under 100 words.
            """
        else:
            product_summaries = []
            for product in products[:3]:
                product_summaries.append(
                    f"• {product['name']} - ${product['price']} ({product['category']}, {product.get('color', 'N/A')})"
                )
            prompt = f"""
            User searched for: "{message}"
            
            Found products:
            {chr(10).join(product_summaries)}
            
            Generate a helpful response that:
            1. Confirms we found great matches
            2. Briefly highlights the products
            3. Asks if they need more details or have preferences
            
            Keep it conversational and under 100 words.
            """
        return await self._call_llm_for_response(prompt)

    async def _generate_order_response(self, message: str, context_data: Optional[Dict] = None) -> str:
        """Generate response for order inquiries"""
        orders = context_data.get("orders", []) if context_data else []

        if not orders:
            prompt = f"""
            User is asking about orders but we couldn't find any orders for them.
            User message: "{message}"
            
            Generate a helpful response that:
            1. Explains we couldn't find orders
            2. Suggests they check their email or order number
            3. Offers to help them place a new order
            
            Keep it helpful and under 75 words.
            """
        else:
            order_summaries = []
            for order in orders[:2]:
                order_summaries.append(
                    f"• Order #{order['order_number']} - {order['status']} (${order['total_amount']})"
                )
            prompt = f"""
            User asked: "{message}"
            
            Their recent orders:
            {chr(10).join(order_summaries)}
            
            Generate a helpful response about their order status.
            Keep it clear and under 75 words.
            """
        return await self._call_llm_for_response(prompt)

    async def _generate_general_response(self, message: str) -> str:
        """Generate response for general inquiries"""
        prompt = f"""
        User said: "{message}"
        
        You are a helpful fashion e-commerce assistant. Generate a friendly response that:
        1. Addresses their message appropriately
        2. Offers to help with shopping or orders
        3. Keeps the conversation engaging
        
        Keep it under 75 words and conversational.
        """
        return await self._call_llm_for_response(prompt)

    # ---------- LLM call helper ----------
    async def _call_llm_for_response(self, prompt: str) -> str:
        """Make LLM call to generate response"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "microsoft/wizardlm-2-8x22b",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.7
                }
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    text = await response.text()
                    if response.status == 200:
                        try:
                            data = json.loads(text)
                            content = (
                                data["choices"][0].get("message", {}).get("content")
                                or data["choices"][0].get("messages", [{}])[0].get("content")
                                or ""
                            )
                            return self._strip_code_fence(content).strip()
                        except Exception as parse_err:
                            logger.error(f"Error parsing LLM response JSON: {parse_err} | Raw: {text}")
                            return "I'm here to help you with your fashion needs! How can I assist you today?"
                    else:
                        logger.error(f"OpenRouter API error: {response.status} | Raw: {text}")
                        return "I'm here to help you with your fashion needs! How can I assist you today?"
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm here to help! Let me know what you're looking for."

    # ---------- Small utilities ----------
    def _fallback_intent_classification(self, message: str) -> Dict[str, Any]:
        """Fallback intent classification using simple rules"""
        message_lower = message.lower()

        order_keywords = ["order", "track", "shipping", "delivery", "status", "cancel", "return"]
        if any(keyword in message_lower for keyword in order_keywords):
            return {
                "intent": "order_inquiry",
                "confidence": 0.7,
                "extracted_info": {"keywords": [word for word in order_keywords if word in message_lower]}
            }

        product_keywords = ["shirt", "dress", "shoes", "jacket", "jeans", "top", "pants", "buy", "find", "looking for"]
        if any(keyword in message_lower for keyword in product_keywords):
            return {
                "intent": "product_search",
                "confidence": 0.7,
                "extracted_info": {"keywords": [word for word in product_keywords if word in message_lower]}
            }

        return {
            "intent": "general",
            "confidence": 0.5,
            "extracted_info": {"keywords": []}
        }

    def _strip_code_fence(self, text: str) -> str:
        """
        Strip code fences like ```json ... ``` or ``` ... ``` and return inner content if present,
        otherwise return the original text.
        """
        if not text:
            return text
        # Remove leading/trailing whitespace
        t = text.strip()

        # Common fenced code block patterns
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```$", t, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1)

        # If text begins with a single code fence line, remove it
        if t.startswith("```") and t.endswith("```"):
            return t[3:-3].strip()

        # Remove triple backticks anywhere
        t = t.replace("```json", "").replace("```", "")
        return t

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to extract a JSON object from provided text robustly.
        Returns parsed dict on success, or None on failure.
        """
        if not text:
            return None

        # 1) Strip fenced block if present
        stripped = self._strip_code_fence(text)

        # 2) Try to find the first JSON object using regex - prefer the largest JSON object
        # We'll search for balanced braces by simple heuristics:
        json_candidates = []

        # a) direct search for { ... } blocks (non-greedy) and also greedy fallback
        for match in re.finditer(r"\{.*?\}", stripped, flags=re.DOTALL):
            json_candidates.append(match.group(0))

        # If nothing found, maybe the model returned pure JSON without fences or with leading text: try greedy
        if not json_candidates:
            greedy = re.search(r"\{(?:.|\s)*\}", stripped, flags=re.DOTALL)
            if greedy:
                json_candidates.append(greedy.group(0))

        # Try parsing candidates, prefer the first that parses
        for candidate in json_candidates:
            try:
                parsed = json.loads(candidate)
                return parsed
            except Exception:
                # try to clean trailing commas (common LLM mistake)
                cleaned = re.sub(r",\s*}", "}", candidate)
                cleaned = re.sub(r",\s*]", "]", cleaned)
                try:
                    parsed = json.loads(cleaned)
                    return parsed
                except Exception:
                    continue

        # 3) As last attempt, if the stripped text itself looks like JSON, try parsing it
        try:
            parsed_whole = json.loads(stripped)
            if isinstance(parsed_whole, dict):
                return parsed_whole
        except Exception:
            pass

        # Nothing workable found
        return None
