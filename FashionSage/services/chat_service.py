import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from models import User, Product, Order, OrderItem, ChatSession, ChatMessage
from services.openrouter_client import OpenRouterClient
from services.simple_search import SimpleSearchService
from schemas import ChatResponse, ProductResponse

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.openrouter = OpenRouterClient()
        self.search_service = SimpleSearchService()
    
    async def process_message(self, message: str, session_id: Optional[str] = None, user_id: Optional[int] = None) -> ChatResponse:
        """Main method to process chat messages"""
        try:
            # Get or create session
            if not session_id:
                session_id = str(uuid.uuid4())
                chat_session = ChatSession(session_id=session_id, user_id=user_id)
                self.db.add(chat_session)
                self.db.commit()
            else:
                chat_session = self.db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                if not chat_session:
                    chat_session = ChatSession(session_id=session_id, user_id=user_id)
                    self.db.add(chat_session)
                    self.db.commit()
            
            # Step 1: Classify intent using OpenRouter LLM
            intent_result = await self.openrouter.classify_intent(message)
            intent = intent_result.get("intent", "general")
            extracted_info = intent_result.get("extracted_info", {})
            
            logger.info(f"Classified intent: {intent} with confidence: {intent_result.get('confidence', 0)}")
            
            # Step 2: Route to appropriate service based on intent
            context_data = {}
            products = []
            orders = []
            
            if intent == "product_search":
                products = await self._handle_product_search(message, extracted_info)
                context_data = {"products": [p.__dict__ if hasattr(p, '__dict__') else p for p in products]}
            
            elif intent == "order_inquiry" and user_id:
                orders = await self._handle_order_inquiry(user_id, extracted_info)
                context_data = {"orders": orders}
            
            elif intent == "order_inquiry" and not user_id:
                # Handle anonymous user asking about orders
                context_data = {"error": "login_required"}
            
            # Step 3: Generate response using LLM
            response_text = await self.openrouter.generate_response(intent, message, context_data)
            
            # Step 4: Save chat message to database
            chat_message = ChatMessage(
                session_id=session_id,
                message=message,
                response=response_text,
                intent=intent
            )
            self.db.add(chat_message)
            self.db.commit()
            
            # Step 5: Format response
            product_responses = []
            if products:
                for product in products[:5]:  # Limit to top 5 results
                    if hasattr(product, '__dict__'):
                        product_dict = product.__dict__.copy()
                        product_dict.pop('_sa_instance_state', None)
                        product_responses.append(ProductResponse(**product_dict))
                    else:
                        # Handle dict format from ChromaDB
                        product_responses.append(ProductResponse(
                            id=product.get('id'),
                            name=product.get('name'),
                            description=product.get('description', ''),
                            price=product.get('price'),
                            category=product.get('category'),
                            color=product.get('color'),
                            size=product.get('size'),
                            brand=product.get('brand'),
                            image_url=product.get('image_url'),
                            stock_quantity=product.get('stock_quantity', 0),
                            tags=product.get('tags'),
                            created_at=product.get('created_at')
                        ))
            
            return ChatResponse(
                response=response_text,
                intent=intent,
                session_id=session_id,
                products=product_responses if product_responses else None,
                orders=orders if orders else None
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ChatResponse(
                response="I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
                intent="error",
                session_id=session_id or str(uuid.uuid4())
            )
    
    async def _handle_product_search(self, message: str, extracted_info: Dict) -> List[Any]:
        """Handle product search using Simple Search"""
        try:
            # Build search filters from extracted info
            filters = {}
            
            if extracted_info.get("category"):
                filters["category"] = extracted_info["category"].lower()
            
            if extracted_info.get("color"):
                filters["color"] = extracted_info["color"].lower()
            
            # Parse price range if mentioned
            if extracted_info.get("price_range"):
                # Simple price parsing - could be enhanced
                price_text = extracted_info["price_range"].lower()
                if "under" in price_text or "less than" in price_text:
                    try:
                        max_price = float(''.join(filter(str.isdigit, price_text)))
                        filters["max_price"] = max_price
                    except:
                        pass
                elif "over" in price_text or "more than" in price_text:
                    try:
                        min_price = float(''.join(filter(str.isdigit, price_text)))
                        filters["min_price"] = min_price
                    except:
                        pass
            
            # Search using Simple Search
            search_results = self.search_service.search_products(
                query=message,
                filters=filters,
                limit=10
            )
            
            # Return the found products
            if search_results:
                return search_results
            
            # Fallback: return empty list if no products found
            query = self.db.query(Product).filter(Product.is_active == True)
            
            # Apply keyword search on name and description
            keywords = extracted_info.get("keywords", [])
            if keywords:
                for keyword in keywords:
                    query = query.filter(
                        func.lower(Product.name).contains(keyword.lower()) |
                        func.lower(Product.description).contains(keyword.lower()) |
                        func.lower(Product.category).contains(keyword.lower())
                    )
            
            # Apply filters
            if filters.get("category"):
                query = query.filter(func.lower(Product.category) == filters["category"])
            if filters.get("color"):
                query = query.filter(func.lower(Product.color) == filters["color"])
            if filters.get("min_price"):
                query = query.filter(Product.price >= filters["min_price"])
            if filters.get("max_price"):
                query = query.filter(Product.price <= filters["max_price"])
            
            return query.limit(10).all()
            
        except Exception as e:
            logger.error(f"Error in product search: {e}")
            return []
    
    async def _handle_order_inquiry(self, user_id: int, extracted_info: Dict) -> List[Dict]:
        """Handle order inquiries from PostgreSQL"""
        try:
            query = self.db.query(Order).filter(Order.user_id == user_id)
            
            # Filter by order number if provided
            order_number = extracted_info.get("order_number")
            if order_number:
                query = query.filter(Order.order_number.ilike(f"%{order_number}%"))
            
            orders = query.order_by(Order.created_at.desc()).limit(5).all()
            
            # Format order data
            order_list = []
            for order in orders:
                order_data = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "total_amount": order.total_amount,
                    "created_at": order.created_at.isoformat(),
                    "item_count": len(order.items) if order.items else 0
                }
                order_list.append(order_data)
            
            return order_list
            
        except Exception as e:
            logger.error(f"Error in order inquiry: {e}")
            return []
    
    async def get_chat_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get chat history for a session"""
        try:
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
            
            history = []
            for msg in reversed(messages):  # Show oldest first
                history.extend([
                    {
                        "type": "user",
                        "content": msg.message,
                        "timestamp": msg.created_at.isoformat()
                    },
                    {
                        "type": "assistant",
                        "content": msg.response,
                        "timestamp": msg.created_at.isoformat(),
                        "intent": msg.intent
                    }
                ])
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
