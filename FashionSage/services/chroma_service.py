import chromadb
import logging
from typing import List, Dict, Any, Optional
from chromadb.utils import embedding_functions
from config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ChromaService:
    def __init__(self):
        """Initialize ChromaDB client and collection"""
        try:
            # ✅ Connect to Chroma running in Docker (HTTP API)
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,   # e.g. "localhost" or "chroma-db"
                port=settings.CHROMA_PORT    # e.g. 8000
            )

            # ✅ Define embedding function (local model)
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

            # ✅ Create or get collection
            self.collection = self.client.get_or_create_collection(
                name="fashion_products",
                metadata={"hnsw:space": "cosine"}  # cosine similarity
            )

            logger.info("ChromaDB (Docker) initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise

    async def add_products(self, products: List[Dict[str, Any]], db=None):  # ✅ added db param
        """Add products to vector database"""
        try:
            if not products:
                return

            documents, metadatas, ids, embeddings = [], [], [], []

            for product in products:
                # Create searchable document text
                doc_text = self._create_product_document(product)
                documents.append(doc_text)

                # ✅ Generate embeddings before inserting
                emb = self.embedding_function([doc_text])[0]
                embeddings.append(emb)

                # Create metadata for filtering
                metadata = {
                    "product_id": product["id"],
                    "name": product["name"],
                    "category": product["category"],
                    "price": float(product["price"]),
                    "brand": product.get("brand", ""),
                    "color": product.get("color", ""),
                    "size": product.get("size", ""),
                    "stock_quantity": product.get("stock_quantity", 0)
                }
                metadatas.append(metadata)
                ids.append(f"product_{product['id']}")

            # ✅ Upsert into collection
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

            logger.info(f"Added {len(products)} products to ChromaDB")

        except Exception as e:
            logger.error(f"Error adding products to ChromaDB: {e}")
            raise

    async def search_products(self, query: str, filters: Optional[Dict] = None, limit: int = 10, db=None):  # ✅ db param
        """Search for products using vector similarity"""
        try:
            # Build where clause
            where_clause = {}
            if filters:
                if filters.get("category"):
                    where_clause["category"] = filters["category"]
                if filters.get("color"):
                    where_clause["color"] = filters["color"]
                if filters.get("brand"):
                    where_clause["brand"] = filters["brand"]
                if filters.get("min_price") is not None:
                    where_clause["price"] = {"$gte": filters["min_price"]}
                if filters.get("max_price") is not None:
                    if "price" not in where_clause:
                        where_clause["price"] = {}
                    where_clause["price"]["$lte"] = filters["max_price"]

            # ✅ Generate embedding for query
            query_embedding = self.embedding_function([query])[0]

            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )

            products = []
            if results.get("documents") and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    product = {
                        "id": metadata["product_id"],
                        "name": metadata["name"],
                        "category": metadata["category"],
                        "price": metadata["price"],
                        "brand": metadata["brand"],
                        "color": metadata["color"],
                        "size": metadata["size"],
                        "stock_quantity": metadata["stock_quantity"],
                        "similarity_score": round(1 - distance, 4),  # convert distance → similarity
                        "relevance_rank": i + 1
                    }
                    products.append(product)

            logger.info(f"Found {len(products)} products for query: '{query}'")
            return products

        except Exception as e:
            logger.error(f"Error searching products in ChromaDB: {e}")
            return []

    def _create_product_document(self, product: Dict) -> str:
        """Create searchable text document from product data"""
        parts = [f"Product: {product['name']}"]

        if product.get("description"):
            parts.append(f"Description: {product['description']}")

        parts.append(f"Category: {product['category']}")
        if product.get("brand"):
            parts.append(f"Brand: {product['brand']}")
        if product.get("color"):
            parts.append(f"Color: {product['color']}")
        if product.get("size"):
            parts.append(f"Size: {product['size']}")

        parts.append(f"Price: ${product['price']}")

        if product.get("tags"):
            tag_text = " ".join(product["tags"]) if isinstance(product["tags"], list) else str(product["tags"])
            parts.append(f"Tags: {tag_text}")

        return " | ".join(parts)

    async def update_product(self, product: Dict[str, Any], db=None):  # ✅ db param
        """Update a single product in the vector database"""
        await self.add_products([product], db=db)

    async def delete_product(self, product_id: int, db=None):  # ✅ db param
        """Delete a product from the vector database"""
        try:
            self.collection.delete(ids=[f"product_{product_id}"])
            logger.info(f"Deleted product {product_id} from ChromaDB")
        except Exception as e:
            logger.error(f"Error deleting product {product_id} from ChromaDB: {e}")

    async def get_collection_stats(self, db=None) -> Dict:  # ✅ db param
        """Get statistics about the product collection"""
        try:
            count = self.collection.count()
            return {
                "total_products": count,
                "collection_name": self.collection.name,
                "embedding_function": "all-MiniLM-L6-v2"
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"total_products": 0}
