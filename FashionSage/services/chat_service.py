import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import User, Product, Order, OrderItem, ChatSession, ChatMessage
from services.openrouter_client import OpenRouterClient
from services.simple_search import HybridSearchService
from schemas import ChatResponse, ProductResponse

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.openrouter = OpenRouterClient()
        # ✅ Pass db_session into HybridSearchService for full hybrid mode
        self.search_service = HybridSearchService(db_session=db)

    # 🔹 Helper: fetch user_id by email from PostgreSQL
    def get_user_id(self, email: str) -> Optional[int]:
        user = self.db.query(User).filter(User.email == email).first()
        return user.id if user else None

    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,   # ✅ new optional argument
    ) -> ChatResponse:
        """Main method to process chat messages"""
        try:
            # --- Step 0: Resolve user_id from email if not provided ---
            if not user_id and user_email:
                user_id = self.get_user_id(user_email)

            # --- Step 1: Get or create session ---
            if not session_id:
                session_id = str(uuid.uuid4())
                chat_session = ChatSession(session_id=session_id, user_id=user_id)
                self.db.add(chat_session)
                self.db.commit()
            else:
                chat_session = (
                    self.db.query(ChatSession)
                    .filter(ChatSession.session_id == session_id)
                    .first()
                )
                if not chat_session:
                    chat_session = ChatSession(session_id=session_id, user_id=user_id)
                    self.db.add(chat_session)
                    self.db.commit()

            # --- Step 2: Classify intent ---
            intent_result = await self.openrouter.classify_intent(message)
            intent = intent_result.get("intent", "general")
            extracted_info = intent_result.get("extracted_info", {})

            logger.info(
                f"Classified intent: {intent} with confidence: {intent_result.get('confidence', 0)}"
            )

            # --- Step 3: Route intent ---
            context_data: Dict[str, Any] = {}
            products: List[Any] = []
            orders: List[Any] = []

            if intent == "product_search":
                products = await self._handle_product_search(message, extracted_info)
                context_data = {
                    "products": [
                        p.__dict__ if hasattr(p, "__dict__") else p for p in products
                    ]
                }

            elif intent == "order_inquiry" and user_id:
                orders = await self._handle_order_inquiry(user_id, extracted_info)
                context_data = {"orders": orders}

            elif intent == "order_inquiry" and not user_id:
                context_data = {"error": "login_required"}

            # --- Step 4: Generate response with LLM ---
            response_text = await self.openrouter.generate_response(
                intent, message, context_data
            )

            # --- Step 5: Save message ---
            chat_message = ChatMessage(
                session_id=session_id,
                message=message,
                response=response_text,
                intent=intent,
            )
            self.db.add(chat_message)
            self.db.commit()

            # --- Step 6: Format final response ---
            product_responses: List[ProductResponse] = []
            if products:
                for product in products[:5]:  # Limit 5
                    if hasattr(product, "__dict__"):
                        product_dict = product.__dict__.copy()
                        product_dict.pop("_sa_instance_state", None)
                        product_responses.append(
                            ProductResponse(
                                id=product_dict.get("id"),
                                name=product_dict.get("name"),
                                description=product_dict.get("description", ""),
                                price=product_dict.get("price", 0.0),
                                category=product_dict.get("category", ""),
                                color=product_dict.get("color"),
                                size=product_dict.get("size"),
                                brand=product_dict.get("brand"),
                                image_url=product_dict.get("image_url"),
                                stock_quantity=product_dict.get("stock_quantity", 0),
                                tags=product_dict.get("tags"),
                                created_at=product_dict.get("created_at"),
                            )
                        )
                    else:
                        product_responses.append(
                            ProductResponse(
                                id=product.get("id"),
                                name=product.get("name"),
                                description=product.get("description", ""),
                                price=product.get("price", 0.0),
                                category=product.get("category", ""),
                                color=product.get("color"),
                                size=product.get("size"),
                                brand=product.get("brand"),
                                image_url=product.get("image_url"),
                                stock_quantity=product.get("stock_quantity", 0),
                                tags=product.get("tags"),
                                created_at=product.get("created_at"),
                            )
                        )

            return ChatResponse(
                response=response_text,
                intent=intent,
                session_id=session_id,
                products=product_responses if product_responses else None,
                orders=orders if orders else None,
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return ChatResponse(
                response="I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
                intent="error",
                session_id=session_id or str(uuid.uuid4()),
            )

    async def _handle_product_search(
        self, message: str, extracted_info: Dict
    ) -> List[Any]:
        """Handle product search using Hybrid Search"""
        try:
            filters: Dict[str, Any] = {}

            # category / color
            if extracted_info.get("category"):
                filters["category"] = extracted_info["category"].lower()
            if extracted_info.get("color"):
                filters["color"] = extracted_info["color"].lower()

            # price parsing
            if extracted_info.get("price_range"):
                price_text = extracted_info["price_range"].lower()
                try:
                    if "under" in price_text or "less than" in price_text:
                        filters["max_price"] = float(
                            "".join(filter(str.isdigit, price_text))
                        )
                    elif "over" in price_text or "more than" in price_text:
                        filters["min_price"] = float(
                            "".join(filter(str.isdigit, price_text))
                        )
                except Exception:
                    pass

            # ✅ Always use HybridSearchService (Chroma + DB + fallback)
            search_results = self.search_service.search_products(
                query=message, filters=filters, limit=10
            )
            return search_results or []

        except Exception as e:
            logger.error(f"Error in product search: {e}", exc_info=True)
            return []

    async def _handle_order_inquiry(
        self, user_id: int, extracted_info: Dict
    ) -> List[Dict]:
        """Handle order inquiries"""
        try:
            query = self.db.query(Order).filter(Order.user_id == user_id)

            # order number filter
            if extracted_info.get("order_number"):
                query = query.filter(
                    Order.order_number.ilike(f"%{extracted_info['order_number']}%")
                )

            orders = query.order_by(Order.created_at.desc()).limit(5).all()

            return [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "total_amount": order.total_amount,
                    "created_at": order.created_at.isoformat(),
                    "item_count": len(order.items) if order.items else 0,
                }
                for order in orders
            ]

        except Exception as e:
            logger.error(f"Error in order inquiry: {e}", exc_info=True)
            return []

    async def get_chat_history(
        self, session_id: str, limit: int = 20
    ) -> List[Dict]:
        """Get chat history"""
        try:
            messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
                .all()
            )

            history: List[Dict[str, Any]] = []
            for msg in reversed(messages):
                history.extend(
                    [
                        {
                            "type": "user",
                            "content": msg.message,
                            "timestamp": msg.created_at.isoformat(),
                        },
                        {
                            "type": "assistant",
                            "content": msg.response,
                            "timestamp": msg.created_at.isoformat(),
                            "intent": msg.intent,
                        },
                    ]
                )

            return history

        except Exception as e:
            logger.error(f"Error getting chat history: {e}", exc_info=True)
            return []
