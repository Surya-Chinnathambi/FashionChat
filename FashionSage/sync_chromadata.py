from services.chroma_service import ChromaService
from database.session import SessionLocal
from database.models import Product

def sync_products_to_chroma():
    db = SessionLocal()
    chroma = ChromaService()

    products = db.query(Product).all()
    if not products:
        print("⚠️ No products found in DB")
        return

    for p in products:
        chroma.add_document(
            doc_id=str(p.id),
            text=f"{p.name}. {p.description}. Category: {p.category}, Color: {p.color}, Size: {p.size}, Brand: {p.brand}. Tags: {','.join(p.tags)}",
            metadata={"id": p.id, "category": p.category, "brand": p.brand, "price": float(p.price)}
        )
    print(f"✅ Synced {len(products)} products into ChromaDB")
