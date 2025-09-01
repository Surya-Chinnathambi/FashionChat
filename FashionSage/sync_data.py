import asyncio
import logging
import uuid
from sqlalchemy.orm import Session

from database import SessionLocal, init_db
from models import Product, User, Order, OrderItem
from services.simple_search import HybridSearchService

# ✅ ChromaDB imports
import chromadb
from chromadb.utils import embedding_functions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------
# Utility: Chroma Client
# -------------------------
def get_chroma_client():
    """Always use HTTP client pointing to local Chroma server"""
    logger.info("Using Chroma HttpClient at http://localhost:8005")
    return chromadb.HttpClient(host="localhost", port=8005)


# -------------------------
# Seed sample DB data
# -------------------------
async def seed_sample_data(db: Session):
    """Seed database with sample fashion products and orders"""
    if db.query(Product).count() > 0:
        logger.info("Sample data already exists, skipping seed")
        return

    logger.info("Seeding sample fashion data...")

    sample_products = [
        Product(
            name="Classic White Button-Down Shirt",
            description="Timeless white cotton button-down shirt perfect for office or casual wear. Premium cotton blend with a tailored fit.",
            price=89.99, category="shirts", color="white", size="M",
            brand="StyleCo", stock_quantity=50,
            tags=["cotton", "business", "classic", "versatile"]
        ),
        Product(
            name="High-Waisted Black Jeans",
            description="Comfortable high-waisted black skinny jeans made from stretch denim. Flattering fit with premium finishing.",
            price=125.00, category="jeans", color="black", size="M",
            brand="DenimPro", stock_quantity=35,
            tags=["denim", "skinny", "stretch", "high-waisted"]
        ),
        Product(
            name="Floral Summer Dress",
            description="Light and airy floral dress perfect for summer occasions. Features a flattering A-line silhouette with flutter sleeves.",
            price=155.00, category="dresses", color="floral", size="L",
            brand="FloralFashion", stock_quantity=25,
            tags=["summer", "floral", "a-line", "lightweight"]
        ),
    ]
    db.add_all(sample_products)

    from services.auth_service import AuthService
    from schemas import UserCreate

    auth_service = AuthService(db)
    try:
        sample_user = auth_service.create_user(UserCreate(
            email="demo@fashionstore.com",
            username="demouser",
            password="demo123"
        ))
    except ValueError:
        sample_user = db.query(User).filter(User.email == "demo@fashionstore.com").first()

    db.commit()

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
        db.flush()

        order_items = [
            OrderItem(order_id=order.id, product_id=sample_products[0].id, quantity=1, price=sample_products[0].price),
            OrderItem(order_id=order.id, product_id=sample_products[1].id, quantity=1, price=sample_products[1].price),
        ]
        db.add_all(order_items)
        order.total_amount = sum(item.price * item.quantity for item in order_items)

    db.commit()
    logger.info(f"✅ Seeded {len(sample_products)} products and 1 sample order")


# -------------------------
# Sync to HybridSearch
# -------------------------
async def sync_products_to_search(db: Session):
    products = db.query(Product).all()
    if not products:
        logger.warning("No products found in DB for search service.")
        return

    logger.info(f"Initializing HybridSearchService with {len(products)} products...")
    HybridSearchService(db_session=db)
    logger.info("✅ HybridSearchService initialized successfully.")


# -------------------------
# Sync to ChromaDB (with batching)
# -------------------------
BATCH_SIZE = 5000  # must be < Chroma’s max (5461)

async def sync_products_to_chroma(db: Session):
    products = db.query(Product).all()
    if not products:
        logger.warning("No products found in DB to sync with Chroma.")
        return

    logger.info(f"Syncing {len(products)} products to ChromaDB...")

    chroma_client = get_chroma_client()
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # ✅ Reset collection each time for clean sync
    try:
        chroma_client.delete_collection("products")
        logger.info("Old Chroma collection 'products' deleted.")
    except Exception:
        logger.info("No old Chroma collection to delete.")

    collection = chroma_client.create_collection(
        name="products",
        embedding_function=embedding_fn
    )

    # ✅ Batch insert to avoid exceeding max size
    for i in range(0, len(products), BATCH_SIZE):
        batch = products[i:i + BATCH_SIZE]
        logger.info(f"🔄 Uploading batch {i // BATCH_SIZE + 1} ({len(batch)} items)...")

        collection.upsert(
            ids=[str(p.id) for p in batch],
            documents=[p.description or p.name for p in batch],
            metadatas=[{
                "name": p.name,
                "category": p.category,
                "color": p.color,
                "brand": p.brand,
                "price": float(p.price)
            } for p in batch]
        )

    count = collection.count()
    logger.info(f"✅ ChromaDB sync completed: {count} products in collection.")


# -------------------------
# Master Sync Pipeline
# -------------------------
async def sync_all():
    logger.info("🚀 Starting data initialization and sync...")
    init_db()

    db = SessionLocal()
    try:
        await seed_sample_data(db)
        await sync_products_to_search(db)
        await sync_products_to_chroma(db)
    finally:
        db.close()

    logger.info("🎉 Data sync pipeline completed successfully!")


if __name__ == "__main__":
    asyncio.run(sync_all())
