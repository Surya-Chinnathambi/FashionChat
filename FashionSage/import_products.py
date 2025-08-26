from chromadb import HttpClient
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product
from config import settings

# Connect to Chroma (running in Docker)
chroma_client = HttpClient(host="localhost", port=8002)
print("Connected to Chroma!")
# Create / get collection
collection = chroma_client.get_or_create_collection(name="products")

# DB session
db: Session = SessionLocal()

# Fetch products from Postgres
products = db.query(Product).all()

if not products:
    print("⚠️ No products in DB to insert into Chroma.")
else:
    for product in products:
        collection.add(
            ids=[str(product.id)],
            documents=[product.description or product.name],
            metadatas=[{
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "color": product.color,
                "brand": product.brand
            }]
        )
    print(f"✅ Indexed {len(products)} products into ChromaDB")
