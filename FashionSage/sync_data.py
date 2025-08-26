import asyncio
import logging
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import Product, User, Order, OrderItem
from services.simple_search import SimpleSearchService
import uuid
from datetime import datetime

# ✅ NEW: standard libs for env/config and typing
import os
from typing import List, Any, Optional

# ✅ NEW: try/except import for requests (used by OpenRouter embedding calls)
try:
    import requests
except Exception:  # pragma: no cover
    requests = None  # Will fallback to default Chroma embedding if missing

# ✅ NEW: ChromaDB imports
import chromadb
from chromadb.utils import embedding_functions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------------
# ✅ NEW: OpenRouter Embedding Function
# -----------------------------------------------------------------------------------
class OpenRouterEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """
    Minimal embedding function that calls OpenRouter's embeddings endpoint.
    - Reads API key from env: OPENROUTER_API_KEY
    - Model from env: OPENROUTER_EMBED_MODEL (default: openai/text-embedding-3-small)
    - Uses 'requests' if available; otherwise raises and the caller should fallback.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/text-embedding-3-small",
        referer: str = "http://localhost:8000",
        x_title: str = "Fashion E-commerce Chatbot",
        timeout: int = 60,
    ):
        if requests is None:
            raise RuntimeError(
                "The 'requests' package is required for OpenRouter embeddings but is not installed."
            )
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is empty or not provided.")

        self.api_key = api_key
        self.model = model
        self.endpoint = "https://openrouter.ai/api/v1/embeddings"
        self.timeout = timeout
        self.session = requests.Session()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optional but recommended by OpenRouter:
            "HTTP-Referer": referer,
            "X-Title": x_title,
        }

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Call OpenRouter embeddings for a batch of texts."""
        payload = {
            "model": self.model,
            "input": texts,
        }
        resp = self.session.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        # Raise if HTTP error
        resp.raise_for_status()
        data = resp.json()
        if "data" not in data:
            raise ValueError(f"Unexpected embedding response: {data}")
        # OpenRouter returns list of objects with 'embedding' key
        vectors = [row["embedding"] for row in data["data"]]
        if len(vectors) != len(texts):
            raise ValueError("Mismatch between inputs and returned embeddings length.")
        return vectors

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        Chroma calls this with a list of strings.
        We batch for safety (though your dataset is small).
        """
        if not texts:
            return []
        # Simple batching to avoid large payloads; adjust if needed
        batch_size = 96
        out: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            vectors = self._embed_batch(chunk)
            out.extend(vectors)
        return out


async def seed_sample_data():
    """Seed database with sample fashion products and orders"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_products = db.query(Product).count()
        if existing_products > 0:
            logger.info("Sample data already exists, skipping seed")
            return
        
        logger.info("Seeding sample fashion data...")
        
        # Sample fashion products
        sample_products = [
            {
                "name": "Classic White Button-Down Shirt",
                "description": "Timeless white cotton button-down shirt perfect for office or casual wear. Premium cotton blend with a tailored fit.",
                "price": 89.99,
                "category": "shirts",
                "color": "white",
                "size": "M",
                "brand": "StyleCo",
                "stock_quantity": 50,
                "tags": ["cotton", "business", "classic", "versatile"]
            },
            {
                "name": "High-Waisted Black Jeans",
                "description": "Comfortable high-waisted black skinny jeans made from stretch denim. Flattering fit with premium finishing.",
                "price": 125.00,
                "category": "jeans",
                "color": "black",
                "size": "M",
                "brand": "DenimPro",
                "stock_quantity": 35,
                "tags": ["denim", "skinny", "stretch", "high-waisted"]
            },
            {
                "name": "Floral Summer Dress",
                "description": "Light and airy floral dress perfect for summer occasions. Features a flattering A-line silhouette with flutter sleeves.",
                "price": 155.00,
                "category": "dresses",
                "color": "floral",
                "size": "L",
                "brand": "FloralFashion",
                "stock_quantity": 25,
                "tags": ["summer", "floral", "a-line", "lightweight"]
            },
            {
                "name": "Leather Ankle Boots",
                "description": "Premium genuine leather ankle boots with a 2-inch heel. Perfect for both casual and professional settings.",
                "price": 189.99,
                "category": "shoes",
                "color": "brown",
                "size": "8",
                "brand": "BootCraft",
                "stock_quantity": 20,
                "tags": ["leather", "ankle", "professional", "heel"]
            },
            {
                "name": "Cozy Knit Sweater",
                "description": "Soft merino wool sweater with a relaxed fit. Ideal for layering during cooler weather.",
                "price": 98.50,
                "category": "sweaters",
                "color": "gray",
                "size": "S",
                "brand": "WoolWorks",
                "stock_quantity": 40,
                "tags": ["wool", "knit", "cozy", "layering"]
            },
            {
                "name": "Designer Handbag",
                "description": "Elegant leather handbag with gold hardware. Features multiple compartments and adjustable strap.",
                "price": 299.99,
                "category": "accessories",
                "color": "black",
                "size": "medium",
                "brand": "LuxBags",
                "stock_quantity": 15,
                "tags": ["leather", "designer", "elegant", "versatile"]
            },
            {
                "name": "Athletic Running Shoes",
                "description": "High-performance running shoes with advanced cushioning and breathable mesh upper.",
                "price": 139.99,
                "category": "shoes",
                "color": "blue",
                "size": "9",
                "brand": "SportTech",
                "stock_quantity": 60,
                "tags": ["athletic", "running", "performance", "breathable"]
            },
            {
                "name": "Silk Scarf",
                "description": "Luxurious silk scarf with vibrant geometric print. Perfect accent piece for any outfit.",
                "price": 75.00,
                "category": "accessories",
                "color": "multicolor",
                "size": "standard",
                "brand": "SilkStyle",
                "stock_quantity": 30,
                "tags": ["silk", "luxury", "geometric", "accent"]
            }
        ]
        
        # Add products to database
        products = []
        for product_data in sample_products:
            product = Product(**product_data)
            products.append(product)
            db.add(product)
        
        # Create sample user
        from services.auth_service import AuthService
        auth_service = AuthService(db)
        
        try:
            from schemas import UserCreate
            sample_user = auth_service.create_user(UserCreate(
                email="demo@fashionstore.com",
                username="demouser",
                password="demo123"
            ))
        except ValueError:
            # User might already exist
            sample_user = db.query(User).filter(User.email == "demo@fashionstore.com").first()
        
        db.commit()
        
        # Create sample order for demo user
        if sample_user:
            order = Order(
                user_id=sample_user.id,
                order_number=f"ORD-{str(uuid.uuid4())[:8].upper()}",
                status="processing",
                total_amount=0,
                shipping_address={
                    "street": "123 Fashion Ave",
                    "city": "Style City",
                    "state": "CA",
                    "zip": "90210",
                    "country": "USA"
                }
            )
            db.add(order)
            db.flush()  # Get order ID
            
            # Add order items
            order_items = [
                OrderItem(
                    order_id=order.id,
                    product_id=products[0].id,  # White shirt
                    quantity=1,
                    price=products[0].price
                ),
                OrderItem(
                    order_id=order.id,
                    product_id=products[1].id,  # Black jeans
                    quantity=1,
                    price=products[1].price
                )
            ]
            
            for item in order_items:
                db.add(item)
            
            order.total_amount = sum(item.price * item.quantity for item in order_items)
        
        db.commit()
        logger.info(f"Successfully seeded {len(products)} products and sample order")
        
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def sync_products_to_search():
    """Initialize simple search service"""
    logger.info("Initializing simple search service...")
    search_service = SimpleSearchService()
    logger.info(f"Simple search initialized with {len(search_service.products)} sample products")


# ✅ NEW: Automatic Chroma Sync (with OpenRouter embeddings if available)
async def sync_products_to_chroma():
    """Sync products from Postgres to ChromaDB"""
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        if not products:
            logger.info("No products found in DB to sync with Chroma.")
            return

        logger.info(f"Syncing {len(products)} products to ChromaDB...")

        # Initialize Chroma client
        chroma_client = chromadb.PersistentClient(path="./chroma_db")

        # --- Embedding function selection (OpenRouter -> fallback Default) ---
        embedding_fn = None
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        embed_model = os.getenv("OPENROUTER_EMBED_MODEL", "openai/text-embedding-3-small").strip()

        if api_key:
            try:
                embedding_fn = OpenRouterEmbeddingFunction(
                    api_key=api_key,
                    model=embed_model,
                    referer=os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:8000"),
                    x_title=os.getenv("OPENROUTER_X_TITLE", "Fashion E-commerce Chatbot"),
                )
                logger.info(f"Using OpenRouter embeddings ({embed_model}) for Chroma.")
            except Exception as e:
                logger.warning(
                    f"OpenRouter embeddings unavailable ({e}). Falling back to DefaultEmbeddingFunction."
                )
                embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        else:
            logger.warning(
                "OPENROUTER_API_KEY not set. Using Chroma DefaultEmbeddingFunction instead."
            )
            embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        # Create or get collection
        collection = chroma_client.get_or_create_collection(
            name="products",
            embedding_function=embedding_fn
        )

        # Insert products into Chroma
        for product in products:
            collection.add(
                ids=[str(product.id)],
                documents=[product.description or product.name],
                metadatas=[{
                    "name": product.name,
                    "category": product.category,
                    "color": product.color,
                    "brand": product.brand,
                    "price": float(product.price)
                }]
            )

        logger.info("ChromaDB sync completed successfully!")

    except Exception as e:
        logger.error(f"Error syncing products to Chroma: {e}")
    finally:
        db.close()


async def main():
    """Main function to initialize and sync data"""
    logger.info("Starting data initialization and sync...")
    
    # Initialize database
    init_db()
    
    # Seed sample data
    await seed_sample_data()
    
    # Initialize search service
    await sync_products_to_search()
    
    # ✅ Sync to Chroma
    await sync_products_to_chroma()
    
    logger.info("Data sync completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
