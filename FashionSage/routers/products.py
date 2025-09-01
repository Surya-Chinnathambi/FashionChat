from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Product
from schemas import ProductResponse
from services.simple_search import HybridSearchService

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Get products with optional filters"""
    query = db.query(Product).filter(Product.is_active == True)
    
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if color:
        query = query.filter(Product.color.ilike(f"%{color}%"))
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    products = query.offset(offset).limit(limit).all()
    
    return [ProductResponse.from_orm(product) for product in products]

@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db)
):
    """Search products using vector similarity"""
    try:
        chroma_service = ChromaService()
        
        # Build filters
        filters = {}
        if category:
            filters["category"] = category.lower()
        if color:
            filters["color"] = color.lower()
        if brand:
            filters["brand"] = brand.lower()
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        
        # Search using ChromaDB
        chroma_results = await chroma_service.search_products(
            query=q,
            filters=filters,
            limit=limit
        )
        
        if chroma_results:
            # Get full product details from PostgreSQL
            product_ids = [result["id"] for result in chroma_results]
            products = db.query(Product).filter(
                Product.id.in_(product_ids),
                Product.is_active == True
            ).all()
            
            # Sort by ChromaDB relevance
            id_to_rank = {result["id"]: result["relevance_rank"] for result in chroma_results}
            products.sort(key=lambda p: id_to_rank.get(p.id, 999))
            
            return [ProductResponse.from_orm(product) for product in products]
        
        return []
        
    except Exception as e:
        # Fallback to database search
        from sqlalchemy import func
        
        query = db.query(Product).filter(Product.is_active == True)
        query = query.filter(
            func.lower(Product.name).contains(q.lower()) |
            func.lower(Product.description).contains(q.lower())
        )
        
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))
        if color:
            query = query.filter(Product.color.ilike(f"%{color}%"))
        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        products = query.limit(limit).all()
        return [ProductResponse.from_orm(product) for product in products]

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get single product by ID"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()
    
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductResponse.from_orm(product)

@router.get("/categories/list")
async def get_categories(db: Session = Depends(get_db)):
    """Get all unique product categories"""
    from sqlalchemy import distinct
    
    categories = db.query(distinct(Product.category)).filter(
        Product.is_active == True,
        Product.category.isnot(None)
    ).all()
    
    return [category[0] for category in categories if category[0]]

@router.get("/brands/list")
async def get_brands(db: Session = Depends(get_db)):
    """Get all unique brands"""
    from sqlalchemy import distinct
    
    brands = db.query(distinct(Product.brand)).filter(
        Product.is_active == True,
        Product.brand.isnot(None)
    ).all()
    
    return [brand[0] for brand in brands if brand[0]]
